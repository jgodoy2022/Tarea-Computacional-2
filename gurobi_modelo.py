import json
import math
import os
import gurobipy as gp
from gurobipy import GRB

RET = "ret"  # Nodo virtual de retorno al depósito (n + 1)

def cargar_instancia(ruta_json):
    with open(ruta_json, 'r') as f:
        data = json.load(f)
    return data

def crear_modelo_convrp(data, log_filename=None):
    model = gp.Model("ConVRP_SLA_Gurobi")
    
    # Redirección opcional de logs a archivo .log
    if log_filename:
        os.makedirs(os.path.dirname(log_filename), exist_ok=True)
        model.Params.LogFile = log_filename

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
                        X[i, j, d, r] = model.addVar(vtype=GRB.BINARY, name=f"X_{i}_{j}_d{d}_r{r}")
                X[depot, i, d, r] = model.addVar(vtype=GRB.BINARY, name=f"X_0_{i}_d{d}_r{r}")
                X[i, RET, d, r] = model.addVar(vtype=GRB.BINARY, name=f"X_{i}_RET_d{d}_r{r}")
            X[depot, RET, d, r] = model.addVar(vtype=GRB.BINARY, name=f"X_0_RET_d{d}_r{r}")

    W = {}
    for d in dias:
        for i in ped[d]:
            lb_v = tw[i]['tw_start'] if i in NTW else 0
            ub_v = tw[i]['tw_end'] if i in NTW else bW
            W[i, d] = model.addVar(lb=lb_v, ub=ub_v, name=f"W_{i}_d{d}")

    dW = {r: model.addVar(lb=aW, ub=bW, name=f"dW_{r}") for r in rutas}
    rW = {(r, d): model.addVar(lb=aW, ub=bW, name=f"rW_{r}_{d}") for r in rutas for d in dias}  # (12)
    model.update()

    # ---------------- OBJETIVO (1) ----------------
    model.setObjective(
        gp.quicksum(td(i, j) * v for (i, j, d, r), v in X.items()), GRB.MINIMIZE)

    # ---------------- RESTRICCIONES ----------------
    # (2) Asignación única cliente-conductor
    for i in clientes:
        model.addConstr(gp.quicksum(Z[i, r] for r in rutas) == 1, name=f"Asig_{i}")

    for d in dias:
        P = ped[d]
        for r in rutas:
            for i in P:
                # (3) Entrada
                model.addConstr(
                    gp.quicksum(X[j, i, d, r] for j in [depot] + P if j != i) == Z[i, r])
                # (4) Salida
                model.addConstr(
                    gp.quicksum(X[i, j, d, r] for j in P + [RET] if j != i) == Z[i, r])
            # (5) Salida y retorno del depósito
            model.addConstr(gp.quicksum(X[depot, j, d, r] for j in P + [RET]) == 1)
            model.addConstr(gp.quicksum(X[i, RET, d, r] for i in P + [depot]) == 1)

            # (7) Sincronización temporal entre clientes
            for i in P:
                for j in P:
                    if i != j:
                        M = bW + st[i] + tt(i, j)
                        model.addConstr(
                            W[i, d] + st[i] + tt(i, j) <= W[j, d] + M * (1 - X[i, j, d, r]))
            for j in P:
                # (9) Salida del depósito
                M = bW + tt(depot, j)
                model.addConstr(dW[r] + tt(depot, j) <= W[j, d] + M * (1 - X[depot, j, d, r]))
                # (10) Retorno al depósito
                M = bW + st[j] + tt(j, depot)
                model.addConstr(
                    W[j, d] + st[j] + tt(j, depot) <= rW[r, d] + M * (1 - X[j, RET, d, r]))

    # (14) Capacidad por ruta y día
    for r in rutas:
        for d in dias:
            model.addConstr(gp.quicksum(q[i, d] * Z[i, r] for i in ped[d]) <= Q)

    model.update()
    return model

def resolver_gurobi(data, es_relajado=False, log_filename=None):
    """Ejecuta Gurobi (Entero o Relajado) y retorna métricas estandarizadas."""
    modelo = crear_modelo_convrp(data, log_filename=log_filename)
    
    if es_relajado:
        modelo = modelo.relax()

    modelo.Params.Threads = 1
    modelo.Params.TimeLimit = 600
    modelo.Params.OutputFlag = 1

    modelo.optimize()

    res = {
        "Solver": "Gurobi",
        "Tipo": "Relajado" if es_relajado else "Entero",
        "Status": modelo.Status,
        "ObjVal": modelo.ObjVal if modelo.SolCount > 0 else None,
        "Tiempo": modelo.Runtime,
        "Nodos": modelo.NodeCount if not es_relajado else 0,
        "Gap": (modelo.MIPGap * 100) if (modelo.SolCount > 0 and not es_relajado) else 0.0
    }
    return res