import json
import os

PATRON_1 = {
        1: [1.0, 0.0, 1.0], 2: [1.0, 1.0, 0.0], 3: [0.0, 1.0, 1.0],
        4: [1.0, 1.0, 1.0], 5: [1.0, 0.0, 1.0], 6: [0.0, 1.0, 1.0],
        7: [1.0, 1.0, 0.0], 8: [1.0, 1.0, 1.0], 9: [0.0, 1.0, 1.0],
        10: [1.0, 0.0, 1.0], 11: [1.0, 1.0, 0.0], 12: [1.0, 1.0, 1.0],
        13: [0.0, 1.0, 1.0], 14: [1.0, 1.0, 0.0], 15: [1.0, 0.0, 1.0]
    }

PATRON_2 = {
        1: [1.0, 1.0, 0.0], 2: [0.0, 1.0, 1.0], 3: [1.0, 0.0, 1.0],
        4: [1.0, 1.0, 1.0], 5: [1.0, 1.0, 0.0], 6: [0.0, 1.0, 1.0],
        7: [1.0, 1.0, 1.0], 8: [1.0, 0.0, 1.0], 9: [1.0, 1.0, 0.0],
        10: [0.0, 1.0, 1.0], 11: [1.0, 1.0, 1.0], 12: [1.0, 0.0, 1.0],
        13: [1.0, 1.0, 0.0], 14: [0.0, 1.0, 1.0], 15: [1.0, 1.0, 1.0]
    }

def parsear_archivo_solomon_txt(ruta_txt, num_clientes=15):
    """
    Lee un archivo .txt estándar de benchmark Solomon (CVRPLIB)
    y extrae el depósito y los primeros `num_clientes` clientes.
    """
    with open(ruta_txt, 'r') as f:
        lineas = f.readlines()

    pos_cust = False
    coords = {}
    demands_raw = {}
    tw_raw = {}
    capacity = 200

    for idx, line in enumerate(lineas):
        line = line.strip()
        if "CAPACITY" in line:
            # La siguiente línea suele traer el número de vehículos y capacidad
            partes = lineas[idx + 1].strip().split()
            if len(partes) >= 2:
                capacity = int(partes[1])
        if "CUST NO." in line:
            pos_cust = idx + 1
            break

    if pos_cust:
        for line in lineas[pos_cust:]:
            partes = line.strip().split()
            if len(partes) >= 7:
                c_id = int(partes[0])
                if c_id > num_clientes:
                    continue
                x, y = float(partes[1]), float(partes[2])
                demand = float(partes[3])
                ready = float(partes[4])
                due = float(partes[5])
                service = float(partes[6])

                coords[c_id] = [x, y]
                demands_raw[c_id] = demand
                tw_raw[c_id] = {
                    "tw_start": ready,
                    "tw_end": due,
                    "service_time": service
                }

    return coords, demands_raw, tw_raw, capacity


def construir_instancia_convrp(coords, demands_base, tw_base, capacidad_q, patron_demanda, num_days=3, num_vehicles=3):
    """
    Transforma datos base de 1 día (Solomon) en una instancia ConVRP de 3 días y 3 vehículos.
    
    patron_demanda: Dict {cliente_id: [q_dia1, q_dia2, q_dia3]}
                    o multiplicadores sobre la demanda base.
    """
    depot_id = 0
    nodos = sorted(list(coords.keys()))
    clientes = [n for n in nodos if n != depot_id]

    # 1. Ventanas de tiempo ajustadas
    # Aseguramos que la ventana del depósito cubra todo el horizonte operativo
    time_windows = {}
    time_windows[str(depot_id)] = {
        "tw_start": tw_base[depot_id]["tw_start"],
        "tw_end": tw_base[depot_id]["tw_end"],
        "service_time": 0.0
    }

    for c in clientes:
        time_windows[str(c)] = {
            "tw_start": float(tw_base[c]["tw_start"]),
            "tw_end": float(tw_base[c]["tw_end"]),
            "service_time": float(tw_base[c]["service_time"])
        }

    # 2. Demandas multi-día
    demands = {}
    demands[str(depot_id)] = [0.0] * num_days

    for c in clientes:
        d_base = demands_base[c]
        if c in patron_demanda:
            mults = patron_demanda[c]
            demands[str(c)] = [round(d_base * m, 1) for m in mults]
        else:
            demands[str(c)] = [round(d_base, 1)] * num_days

    # 3. Coordenadas
    coordinates = {str(k): v for k, v in coords.items()}

    instancia_dict = {
        "depot": depot_id,
        "nodes": nodos,
        "num_days": num_days,
        "num_vehicles": num_vehicles,
        "capacity": capacidad_q,
        "demands": demands,
        "time_windows": time_windows,
        "coordinates": coordinates
    }

    return instancia_dict

if __name__ == "__main__":
    nombre_instancia = "R101"
    
    print("Generando instancias adaptadas para ConVRP...")
    coords, demands, tw, capacity = parsear_archivo_solomon_txt(f"instancias/{nombre_instancia}.txt", 15)
    instancia = construir_instancia_convrp(coords, demands, tw, capacity, PATRON_2)
    
    os.makedirs("instancias", exist_ok=True)
    with open(f"instancias/{nombre_instancia}.json", "w") as f:
        json.dump(instancia, f, indent=2)
    