import json
import os

os.makedirs("instancias", exist_ok=True)

# Nodos C101 con ventanas ampliadas para dar holgura de ruteo
c101_nodes = {
    0:  {"x": 40, "y": 50, "demand": 0,  "ready": 0,   "due": 2000, "service": 0},
    1:  {"x": 45, "y": 68, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    2:  {"x": 45, "y": 70, "demand": 30, "ready": 0,   "due": 1500, "service": 30},
    3:  {"x": 42, "y": 66, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    4:  {"x": 42, "y": 68, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    5:  {"x": 42, "y": 65, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    6:  {"x": 40, "y": 69, "demand": 20, "ready": 0,   "due": 1500, "service": 30},
    7:  {"x": 40, "y": 66, "demand": 20, "ready": 0,   "due": 1500, "service": 30},
    8:  {"x": 38, "y": 68, "demand": 20, "ready": 0,   "due": 1500, "service": 30},
    9:  {"x": 38, "y": 70, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    10: {"x": 35, "y": 66, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    11: {"x": 35, "y": 69, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    12: {"x": 25, "y": 85, "demand": 20, "ready": 0,   "due": 1500, "service": 30},
    13: {"x": 22, "y": 75, "demand": 30, "ready": 0,   "due": 1500, "service": 30},
    14: {"x": 22, "y": 85, "demand": 10, "ready": 0,   "due": 1500, "service": 30},
    15: {"x": 20, "y": 80, "demand": 40, "ready": 0,   "due": 1500, "service": 30}
}

# Nodos R101 con ventanas ampliadas
r101_nodes = {
    0:  {"x": 35, "y": 35, "demand": 0,  "ready": 0,   "due": 2000, "service": 0},
    1:  {"x": 41, "y": 49, "demand": 10, "ready": 0,   "due": 1500, "service": 10},
    2:  {"x": 35, "y": 17, "demand": 7,  "ready": 0,   "due": 1500, "service": 10},
    3:  {"x": 55, "y": 45, "demand": 13, "ready": 0,   "due": 1500, "service": 10},
    4:  {"x": 55, "y": 20, "demand": 19, "ready": 0,   "due": 1500, "service": 10},
    5:  {"x": 15, "y": 30, "demand": 26, "ready": 0,   "due": 1500, "service": 10},
    6:  {"x": 25, "y": 30, "demand": 3,  "ready": 0,   "due": 1500, "service": 10},
    7:  {"x": 20, "y": 50, "demand": 5,  "ready": 0,   "due": 1500, "service": 10},
    8:  {"x": 10, "y": 43, "demand": 9,  "ready": 0,   "due": 1500, "service": 10},
    9:  {"x": 55, "y": 60, "demand": 16, "ready": 0,   "due": 1500, "service": 10},
    10: {"x": 30, "y": 60, "demand": 16, "ready": 0,   "due": 1500, "service": 10},
    11: {"x": 20, "y": 65, "demand": 12, "ready": 0,   "due": 1500, "service": 10},
    12: {"x": 50, "y": 35, "demand": 19, "ready": 0,   "due": 1500, "service": 10},
    13: {"x": 30, "y": 25, "demand": 23, "ready": 0,   "due": 1500, "service": 10},
    14: {"x": 15, "y": 10, "demand": 20, "ready": 0,   "due": 1500, "service": 10},
    15: {"x": 30, "y": 5,  "demand": 8,  "ready": 0,   "due": 1500, "service": 10}
}

def construir_json(nodes, name, capacity):
    return {
        "name": name,
        "num_clients": 15,
        "num_days": 3,
        "num_vehicles": 3,
        "capacity": capacity,
        "depot": 0,
        "nodes": list(range(16)),
        "coordinates": {str(i): [data["x"], data["y"]] for i, data in nodes.items()},
        "demands": {
            str(i): [
                nodes[i]["demand"] if i % 2 != 0 else 0,
                nodes[i]["demand"] if i % 3 != 0 else 0,
                nodes[i]["demand"] if (i % 2 == 0 or i % 3 == 0) else 0
            ] for i in range(1, 16)
        },
        "time_windows": {
            str(i): {
                "tw_start": data["ready"],
                "tw_end": data["due"],
                "service_time": data["service"]
            } for i, data in nodes.items()
        }
    }

# Generar ambas instancias
with open("instancias/instancia_1.json", "w") as f:
    json.dump(construir_json(c101_nodes, "Instancia_1_C101_3D", capacity=100), f, indent=2)

with open("instancias/instancia_2.json", "w") as f:
    json.dump(construir_json(r101_nodes, "Instancia_2_R101_3D", capacity=80), f, indent=2)

print("¡Instancias regeneradas con éxito!")