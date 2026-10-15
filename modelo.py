import json
import math
import gurobipy as gp
from gurobipy import GRB

def cargar_instancia(ruta_json):
    with open(ruta_json, 'r') as f:
        data = json.load(f)
    return data

def crear_modelo_convrp(data):

    model = gp.Model("ConVRP_SLA_Reducido")
    
    # Extraer conjuntos y datos básicos
    clientes = [n for n in data['nodes'] if n != data['depot']]
    depot = data['depot']
    nodos = data['nodes']
    dias = list(range(1, data['num_days'] + 1))
    vehiculos = list(range(1, data['num_vehicles'] + 1))
    
    demands = {int(k): v for k, v in data['demands'].items()}
    tw = {int(k): v for k, v in data['time_windows'].items()}
    coords = {int(k): v for k, v in data['coordinates'].items()}
    Q = data['capacity']
    
    # Calcular matriz de distancias euclidianas t_ij
    dist = {}
    for i in nodos:
        for j in nodos:
            dist[(i, j)] = math.hypot(coords[i][0] - coords[j][0], coords[i][1] - coords[j][1])

    #1. VARIABLES DE DECISIÓN
    
    X = {}
    for d in dias:
        for k in vehiculos:
            for i in nodos:
                for j in nodos:
                    if i != j:
                        X[i, j, d, k] = model.addVar(vtype=GRB.BINARY, name=f"X_{i}_{j}_d{d}_k{k}")

    T = {}
    for d in dias:
        for i in nodos:
            # Definir cotas iniciales basadas directamente en la ventana de tiempo del nodo para evitar infeasibilidad
            lb_val = tw[i]['tw_start']
            ub_val = tw[i]['tw_end']
            T[i, d] = model.addVar(vtype=GRB.CONTINUOUS, lb=lb_val, ub=ub_val, name=f"T_{i}_d{d}")

    model.update()

    # 2. FUNCIÓN OBJETIVO (1): Minimizar distancia total
 
    obj = gp.quicksum(dist[i, j] * X[i, j, d, k] 
                      for d in dias 
                      for k in vehiculos 
                      for i in nodos for j in nodos if i != j)
    model.setObjective(obj, GRB.MINIMIZE)

    # 3. RESTRICCIONES PRINCIPALES
    
    # A. Restricción de Capacidad del Vehículo (14)
    for d in dias:
        for k in vehiculos:
            model.addConstr(
                gp.quicksum(demands.get(i, [0,0,0])[d-1] * X[i, j, d, k] 
                            for i in clientes for j in nodos if i != j) <= Q,
                name=f"Capacidad_d{d}_k{k}"
            )

    # B. Restricciones de Visita y Flujo / Grado (3)-(4)
    for d in dias:
        for i in clientes:
            demanda_cliente_dia = demands.get(i, [0,0,0])[d-1]
            requiere_visita = 1 if demanda_cliente_dia > 0 else 0
            
            model.addConstr(
                gp.quicksum(X[j, i, d, k] for k in vehiculos for j in nodos if j != i) == requiere_visita,
                name=f"Visita_Entrada_{i}_d{d}"
            )

    # C. Conservación de flujo en los clientes
    for d in dias:
        for k in vehiculos:
            for j in clientes:
                model.addConstr(
                    gp.quicksum(X[i, j, d, k] for i in nodos if i != j) == 
                    gp.quicksum(X[j, i, d, k] for i in nodos if i != j),
                    name=f"Flujo_{j}_d{d}_k{k}"
                )

    # D. Salida y retorno del Depósito (5)
    for d in dias:
        for k in vehiculos:
            model.addConstr(
                gp.quicksum(X[depot, j, d, k] for j in clientes) == 
                gp.quicksum(X[j, depot, d, k] for j in clientes),
                name=f"Deposito_Balance_d{d}_k{k}"
            )
            model.addConstr(
                gp.quicksum(X[depot, j, d, k] for j in clientes) <= 1,
                name=f"Max_Salida_Deposito_d{d}_k{k}"
            )

    # E. Ventanas de Tiempo y Seguimiento con Big-M adaptado al horizonte del depósito
        BigM = tw[depot]['tw_end'] * 2 
    for d in dias:
        for k in vehiculos:
            for i in nodos:
                for j in nodos:
                    if i != j:
                        model.addConstr(
                            T[i, d] + tw[i]['service_time'] + dist[i, j] - T[j, d] <= BigM * (1 - X[i, j, d, k]),
                            name=f"BigM_{i}_{j}_d{d}_k{k}"
                        )

    model.update()
    return model

if __name__ == "__main__":
    datos = cargar_instancia("instancias/recortado.json")
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
    
    if modelo.Status == GRB.OPTIMAL or modelo.Status == GRB.SUBOPTIMAL:
        print(f"\n--- RESULTADOS ---")
        print(f"Valor objetivo (Distancia Total): {modelo.ObjVal:.2f}")
        print(f"Tiempo de resolución: {modelo.Runtime:.2f} segundos")
        print(f"Gap final: {modelo.MIPGap * 100:.2f}%")
    else:
        print(f"El modelo no encontró una solución óptima en este estado (Código de estado: {modelo.Status})")