import json
import math
import os
from docplex.mp.model import Model

RET = "ret"  # Nodo virtual de retorno al depósito (n + 1)


def cargar_instancia(ruta_json):
    with open(ruta_json, 'r') as f:
        data = json.load(f)
    return data


def crear_modelo_convrp(data):
    model = Model(name="ConVRP_SLA_CPLEX")

    depot = data['depot']
    clientes = [n for n in data['nodes'] if n != depot]
    dias = list(range(1, data['num_days'] + 1))
    rutas = list(range(1, data['num_vehicles'] + 1))

    demands = {int(k): v for k, v in data['demands'].items()}
    tw = {int(k): v for k, v in data['time_windows'].items()}
    coords = {int(k): v for k, v in data['coordinates'].items()}
    Q = data['capacity']
    aW, bW = tw[depot]['tw_start'], tw[depot]['tw_end']

    q = {(i, d): demands.get(i, [0] * len(dias))[d - 1] for i in clientes for d in dias}
    st = {i: tw[i].get('service_time', 0) for i in clientes}
    st[depot] = 0

    # Nodos con pedido activo cada día
    ped = {d: [i for i in clientes if q[i, d] > 0] for d in dias}
    # Nodos con ventana de tiempo propia/restringida
    NTW = {i for i in clientes if (tw[i]['tw_start'], tw[i]['tw_end']) != (aW, bW)}

    def td(i, j):
        ni = depot if i == RET else i
        nj = depot if j == RET else j
        return math.hypot(coords[ni][0] - coords[nj][0], coords[ni][1] - coords[nj][1])
    tt = td  # velocidad unitaria

    # ---------------- VARIABLES ----------------
    # Z[i, r] = 1 si el cliente i es atendido por la ruta r
    Z = {(i, r): model.binary_var(name=f"Z_{i}_r{r}")
         for i in clientes for r in rutas}

    # X[i, j, d, r] = 1 si la ruta r recorre el arco (i,j) en el día d
    X = {}
    for d in dias:
        P = ped[d]
        for r in rutas:
            for i in P:
                for j in P:
                    if i != j:
                        X[i, j, d, r] = model.binary_var(name=f"X_{i}_{j}_d{d}_r{r}")
                X[depot, i, d, r] = model.binary_var(name=f"X_0_{i}_d{d}_r{r}")
                X[i, RET, d, r] = model.binary_var(name=f"X_{i}_RET_d{d}_r{r}")
            X[depot, RET, d, r] = model.binary_var(name=f"X_0_RET_d{d}_r{r}")

    # W[i, d] = tiempo de inicio de servicio del cliente i en el día d
    W = {}
    for d in dias:
        for i in ped[d]:
            lb_v = tw[i]['tw_start'] if i in NTW else 0
            ub_v = tw[i]['tw_end'] if i in NTW else bW
            W[i, d] = model.continuous_var(lb=lb_v, ub=ub_v, name=f"W_{i}_d{d}")

    # dW[r] = tiempo de salida del depósito de la ruta r
    dW = {r: model.continuous_var(lb=aW, ub=bW, name=f"dW_{r}") for r in rutas}
    # rW[r, d] = tiempo de retorno al depósito de la ruta r en el día d
    rW = {(r, d): model.continuous_var(lb=aW, ub=bW, name=f"rW_{r}_{d}")
          for r in rutas for d in dias}

    # ---------------- OBJETIVO (1) ----------------
    model.minimize(
        model.sum(td(i, j) * X[i, j, d, r] for (i, j, d, r) in X))

    # ---------------- RESTRICCIONES ----------------
    # (2) Asignación única cliente-conductor
    for i in clientes:
        model.add_constraint(model.sum(Z[i, r] for r in rutas) == 1,
                             ctname=f"Asig_{i}")

    for d in dias:
        P = ped[d]
        for r in rutas:
            for i in P:
                # (3) Entrada
                model.add_constraint(
                    model.sum(X[j, i, d, r] for j in [depot] + P if j != i) == Z[i, r],
                    ctname=f"Entrada_{i}_d{d}_r{r}")
                # (4) Salida
                model.add_constraint(
                    model.sum(X[i, j, d, r] for j in P + [RET] if j != i) == Z[i, r],
                    ctname=f"Salida_{i}_d{d}_r{r}")
            # (5) Salida y retorno del depósito
            model.add_constraint(
                model.sum(X[depot, j, d, r] for j in P + [RET]) == 1,
                ctname=f"DepSalida_d{d}_r{r}")
            model.add_constraint(
                model.sum(X[i, RET, d, r] for i in P + [depot]) == 1,
                ctname=f"DepRetorno_d{d}_r{r}")

            # (7) Sincronización temporal entre clientes
            for i in P:
                for j in P:
                    if i != j:
                        M = bW + st[i] + tt(i, j)
                        model.add_constraint(
                            W[i, d] + st[i] + tt(i, j) <= W[j, d] + M * (1 - X[i, j, d, r]),
                            ctname=f"TSync_{i}_{j}_d{d}_r{r}")
            for j in P:
                # (9) Salida del depósito
                M = bW + tt(depot, j)
                model.add_constraint(
                    dW[r] + tt(depot, j) <= W[j, d] + M * (1 - X[depot, j, d, r]),
                    ctname=f"DepOut_{j}_d{d}_r{r}")
                # (10) Retorno al depósito
                M = bW + st[j] + tt(j, depot)
                model.add_constraint(
                    W[j, d] + st[j] + tt(j, depot) <= rW[r, d] + M * (1 - X[j, RET, d, r]),
                    ctname=f"DepIn_{j}_d{d}_r{r}")

    # (14) Capacidad por ruta y día
    for r in rutas:
        for d in dias:
            model.add_constraint(
                model.sum(q[i, d] * Z[i, r] for i in ped[d]) <= Q,
                ctname=f"Cap_r{r}_d{d}")

    return model


def resolver_cplex(data, es_relajado=False, log_filename=None):
    """Ejecuta CPLEX (Entero o Relajado) y retorna métricas estandarizadas."""
    modelo = crear_modelo_convrp(data)

    # Configuración del solver
    modelo.parameters.threads = 1
    modelo.parameters.timelimit = 600

    if es_relajado:
        # Relajación lineal continua: clonar y convertir binarias a continuas
        modelo_usado = modelo.clone()
        for var in modelo_usado.iter_variables():
            if var.is_binary() or var.is_integer():
                modelo_usado.change_var_types([var], ['C'])
    else:
        modelo_usado = modelo

    # Redirigir log a archivo si se especifica
    if log_filename:
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        log_file = open(log_filename, 'w')
        modelo_usado.set_log_output(log_file)
        sol = modelo_usado.solve(log_output=False)
        log_file.close()
    else:
        sol = modelo_usado.solve(log_output=True)

    # Recopilar métricas
    details = modelo_usado.solve_details
    if sol is not None:
        obj_val = sol.objective_value
        tiempo  = details.time
        nodos   = details.nb_nodes_processed if not es_relajado else 0
        gap     = (details.mip_relative_gap * 100
                   if (not es_relajado and details.mip_relative_gap is not None)
                   else 0.0)
        status_str = details.status
    else:
        obj_val    = None
        tiempo     = details.time if details else 0
        nodos      = 0
        gap        = 0.0
        status_str = details.status if details else "No solution"

    res = {
        "Solver":    "CPLEX",
        "Tipo":      "Relajado" if es_relajado else "Entero",
        "Status":    status_str,
        "ObjVal":    obj_val,
        "Tiempo":    tiempo,
        "Nodos":     nodos,
        "Gap":       gap,
    }
    return res


if __name__ == "__main__":
    datos = cargar_instancia("instancias/instancia_1.json")
    modelo = crear_modelo_convrp(datos)

    print("¡Modelo creado exitosamente con CPLEX (docplex)!")
    print(f"Número de variables: {modelo.number_of_variables}")
    print(f"Número de restricciones: {modelo.number_of_constraints}")

    modelo.parameters.threads = 1
    modelo.parameters.timelimit = 600

    print("\nEjecutando optimización...")
    sol = modelo.solve(log_output=True)

    if sol is not None:
        print(f"\n--- RESULTADOS ---")
        print(f"Valor objetivo (Distancia Total): {sol.objective_value:.2f}")
        print(f"Tiempo de resolución: {modelo.solve_details.time:.2f} segundos")
        mip_gap = modelo.solve_details.mip_relative_gap
        if mip_gap is not None:
            print(f"Gap final: {mip_gap * 100:.2f}%")
    else:
        print(f"El modelo no encontró una solución. Status: {modelo.solve_details.status}")
