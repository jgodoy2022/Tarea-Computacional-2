import json
import math
import gurobipy as gp
from gurobipy import GRB

RET = "ret" # Nodo de retorno al deposito (n + 1)

def cargar_instancia(ruta_json):
    with open(ruta_json, 'r') as f:
        data = json.load(f)
    return data

def crear_modelo_convrp(data):

    model = gp.Model("ConVRP_SLA_Reducido")

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

    # Nodos con pedido cada día (preprocesamiento de arcos)
    ped = {d: [i for i in clientes if q[i, d] > 0] for d in dias}
    # Nodos con ventana propia (NTW)
    NTW = {i for i in clientes
           if (tw[i]['tw_start'], tw[i]['tw_end']) != (aW, bW)}

    def td(i, j):
        i = depot if i == RET else i
        j = depot if j == RET else j
        return math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])
    tt = td  # velocidad unitaria

    # ---------------- VARIABLES ----------------
    Z = {(i, r): model.addVar(vtype=GRB.BINARY, name=f"Z_{i}_r{r}")
         for i in clientes for r in rutas}

    X = {}
    for d in dias:
        P = ped[d]
        for r in rutas:
            for i in P:
                for j in P:
                    if i != j:
                        X[i, j, d, r] = model.addVar(vtype=GRB.BINARY)
                X[depot, i, d, r] = model.addVar(vtype=GRB.BINARY)
                X[i, RET, d, r] = model.addVar(vtype=GRB.BINARY)
            X[depot, RET, d, r] = model.addVar(vtype=GRB.BINARY)  # ruta no sale

    W = {}
    for d in dias:
        for i in ped[d]:
            if i in NTW:
                W[i, d] = model.addVar(lb=tw[i]['tw_start'], ub=tw[i]['tw_end'])  # (8)
            else:
                W[i, d] = model.addVar(lb=0, ub=bW)
    dW = {r: model.addVar(lb=aW, ub=bW, name=f"dW_{r}") for r in rutas}          # (11)
    rW = {(r, d): model.addVar(lb=0, ub=bW, name=f"rW_{r}_{d}")                   # (12)
          for r in rutas for d in dias}
    model.update()

    # ---------------- OBJETIVO (1) ----------------
    model.setObjective(
        gp.quicksum(td(i, j) * v for (i, j, d, r), v in X.items()), GRB.MINIMIZE)

    # ---------------- RESTRICCIONES ----------------
    # (2) cada cliente en una sola ruta
    for i in clientes:
        model.addConstr(gp.quicksum(Z[i, r] for r in rutas) == 1)

    for d in dias:
        P = ped[d]
        for r in rutas:
            for i in P:
                # (3) entrada
                model.addConstr(
                    gp.quicksum(X[j, i, d, r] for j in [depot] + P if j != i) == Z[i, r])
                # (4) salida
                model.addConstr(
                    gp.quicksum(X[i, j, d, r] for j in P + [RET] if j != i) == Z[i, r])
            # (5) sale exactamente una vez (arco ficticio si no opera) y retorna una vez
            model.addConstr(
                gp.quicksum(X[depot, j, d, r] for j in P + [RET]) == 1)
            model.addConstr(
                gp.quicksum(X[i, RET, d, r] for i in P + [depot]) == 1)

            # (7) tiempos entre clientes
            for i in P:
                for j in P:
                    if i != j:
                        M = bW + st[i] + tt(i, j)
                        model.addConstr(
                            W[i, d] + st[i] + tt(i, j) <= W[j, d] + M * (1 - X[i, j, d, r]))
            for j in P:
                # (9) salida del depósito
                M = bW + tt(depot, j)
                model.addConstr(dW[r] + tt(depot, j) <= W[j, d] + M * (1 - X[depot, j, d, r]))
                # (10) retorno al depósito
                M = bW + st[j] + tt(j, depot)
                model.addConstr(
                    W[j, d] + st[j] + tt(j, depot) <= rW[r, d] + M * (1 - X[j, RET, d, r]))

    # (14) capacidad vía Z
    for r in rutas:
        for d in dias:
            model.addConstr(gp.quicksum(q[i, d] * Z[i, r] for i in ped[d]) <= Q)

    model.update()
    return model

if __name__ == "__main__":
    datos = cargar_instancia("instancias/instancia_1.json")
    modelo = crear_modelo_convrp(datos)
    
    modelo.update()
    print("¡Modelo creado exitosamente con Gurobi!")
    print(f"Número de variables: {modelo.NumVars}")
    print(f"Número de restricciones: {modelo.NumConstrs}")
    
    # Configuración base obligatoria
    modelo.Params.Threads = 1
    modelo.Params.TimeLimit = 600
    
    print("\nEjecutando optimización (Baseline con límites correctos de ventanas de tiempo)...")
    modelo.optimize()
    
    if modelo.Status in [GRB.OPTIMAL, GRB.SUBOPTIMAL, GRB.TIME_LIMIT]:
        print(f"\n--- RESULTADOS ---")
        print(f"Valor objetivo (Distancia Total): {modelo.ObjVal:.2f}")
        print(f"Tiempo de resolución: {modelo.Runtime:.2f} segundos")
        print(f"Gap final: {modelo.MIPGap * 100:.2f}%")
    else:
        print(f"El modelo no encontró una solución óptima en este estado (Código de estado: {modelo.Status})")