import json
import os

# Datos reales del 0 al 15 extraídos de C101
c101_nodes = {
    0:  {"x": 40, "y": 50, "demand": 0,  "ready": 0,   "due": 1236, "service": 0},
    1:  {"x": 45, "y": 68, "demand": 10, "ready": 912, "due": 967,  "service": 90},
    2:  {"x": 45, "y": 70, "demand": 30, "ready": 825, "due": 870,  "service": 90},
    3:  {"x": 42, "y": 66, "demand": 10, "ready": 65,  "due": 146,  "service": 90},
    4:  {"x": 42, "y": 68, "demand": 10, "ready": 727, "due": 782,  "service": 90},
    5:  {"x": 42, "y": 65, "demand": 10, "ready": 15,  "due": 67,   "service": 90},
    6:  {"x": 40, "y": 69, "demand": 20, "ready": 621, "due": 702,  "service": 90},
    7:  {"x": 40, "y": 66, "demand": 20, "ready": 170, "due": 225,  "service": 90},
    8:  {"x": 38, "y": 68, "demand": 20, "ready": 255, "due": 324,  "service": 90},
    9:  {"x": 38, "y": 70, "demand": 10, "ready": 534, "due": 605,  "service": 90},
    10: {"x": 35, "y": 66, "demand": 10, "ready": 357, "due": 410,  "service": 90},
    11: {"x": 35, "y": 69, "demand": 10, "ready": 448, "due": 505,  "service": 90},
    12: {"x": 25, "y": 85, "demand": 20, "ready": 652, "due": 721,  "service": 90},
    13: {"x": 22, "y": 75, "demand": 30, "ready": 30,  "due": 92,   "service": 90},
    14: {"x": 22, "y": 85, "demand": 10, "ready": 567, "due": 620,  "service": 90},
    15: {"x": 20, "y": 80, "demand": 40, "ready": 384, "due": 429,  "service": 90}
}

# Datos reales del 0 al 15 extraídos de R101
r101_nodes = {
    0:  {"x": 35, "y": 35, "demand": 0,  "ready": 0,   "due": 230, "service": 0},
    1:  {"x": 41, "y": 49, "demand": 10, "ready": 161, "due": 171, "service": 10},
    2:  {"x": 35, "y": 17, "demand": 7,  "ready": 50,  "due": 60,  "service": 10},
    3:  {"x": 55, "y": 45, "demand": 13, "ready": 116, "due": 126, "service": 10},
    4:  {"x": 55, "y": 20, "demand": 19, "ready": 149, "due": 159, "service": 10},
    5:  {"x": 15, "y": 30, "demand": 26, "ready": 34,  "due": 44,  "service": 10},
    6:  {"x": 25, "y": 30, "demand": 3,  "ready": 99,  "due": 109, "service": 10},
    7:  {"x": 20, "y": 50, "demand": 5,  "ready": 81,  "due": 91,  "service": 10},
    8:  {"x": 10, "y": 43, "demand": 9,  "ready": 95,  "due": 105, "service": 10},
    9:  {"x": 55, "y": 60, "demand": 16, "ready": 97,  "due": 107, "service": 10},
    10: {"x": 30, "y": 60, "demand": 16, "ready": 124, "due": 134, "service": 10},
    11: {"x": 20, "y": 65, "demand": 12, "ready": 67,  "due": 77,  "service": 10},
    12: {"x": 50, "y": 35, "demand": 19, "ready": 63,  "due": 73,  "service": 10},
    13: {"x": 30, "y": 25, "demand": 23, "ready": 159, "due": 169, "service": 10},
    14: {"x": 15, "y": 10, "demand": 20, "ready": 32,  "due": 42,  "service": 10},
    15: {"x": 30, "y": 5,  "demand": 8,  "ready": 61,  "due": 71,  "service": 10}
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
        # Demandas asignadas a los 3 días [Día 1, Día 2, Día 3]
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

# Instancia 1: C101
with open("instancias/instancia_1.json", "w") as f:
    json.dump(construir_json(c101_nodes, "Instancia_1_C101_3D", capacity=50), f, indent=2)

# Instancia 2: R101
with open("instancias/instancia_2.json", "w") as f:
    json.dump(construir_json(r101_nodes, "Instancia_2_R101_3D", capacity=40), f, indent=2)