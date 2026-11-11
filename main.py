import os
import pandas as pd
from gurobi_modelo import cargar_instancia, resolver_gurobi

def ejecutar_benchmark():
    os.makedirs("logs", exist_ok=True)
    
    instancias = {
        "C108": "instancias/C108.json",
        "R108": "instancias/R108.json"
    }

    resultados = []

    for nombre_inst, ruta in instancias.items():
        print(f"Procesando {nombre_inst}...")
        datos = cargar_instancia(ruta)

        # Relajacion Continua
        log_g_rel = f"logs/gurobi_{nombre_inst}_relajado.log"
        res_g_rel = resolver_gurobi(datos, es_relajado=True, log_filename=log_g_rel)
        res_g_rel["Instancia"] = nombre_inst
        resultados.append(res_g_rel)

        # Modelo Entero
        log_g_ent = f"logs/gurobi_{nombre_inst}_entero.log"
        res_g_ent = resolver_gurobi(datos, es_relajado=False, log_filename=log_g_ent)
        res_g_ent["Instancia"] = nombre_inst
        resultados.append(res_g_ent)

    # Exportacion y despliegue de resultados
    df = pd.DataFrame(resultados)
    columnas = ["Instancia", "Solver", "Tipo", "ObjVal", "Tiempo", "Nodos", "Gap"]
    df = df[columnas]

    print("\nResultados Gurobi:")
    print(df.to_string(index=False))

    df.to_csv("resultados_gurobi.csv", index=False)

if __name__ == "__main__":
    ejecutar_benchmark()