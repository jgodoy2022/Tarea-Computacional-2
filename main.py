import os
import pandas as pd
from gurobi_modelo import cargar_instancia, resolver_gurobi
from cplex_modelo import resolver_cplex

# ── Directorios de salida ────────────────────────────────────────────────────
DIR_LOGS = "logs"
DIR_DATA = "data"
CSV_SALIDA = os.path.join(DIR_DATA, "resultados.csv")

# ── Instancias a evaluar ─────────────────────────────────────────────────────
INSTANCIAS = {
    "C108": "instancias/C108.json",
    "R108": "instancias/R108.json",
}

# ── Columnas del CSV de resultados ───────────────────────────────────────────
COLUMNAS = ["Instancia", "Solver", "Tipo", "ObjVal", "Tiempo", "Nodos", "Gap", "Status"]


def ejecutar_benchmark():
    os.makedirs(DIR_LOGS, exist_ok=True)
    os.makedirs(DIR_DATA, exist_ok=True)

    resultados = []

    for nombre_inst, ruta in INSTANCIAS.items():
        print(f"\n{'='*60}")
        print(f"  Instancia: {nombre_inst}")
        print(f"{'='*60}")
        datos = cargar_instancia(ruta)

        # ── GUROBI ──────────────────────────────────────────────────────────
        print(f"\n[Gurobi] Relajación lineal continua — {nombre_inst}")
        log = os.path.join(DIR_LOGS, f"gurobi_{nombre_inst}_relajado.log")
        res = resolver_gurobi(datos, es_relajado=True, log_filename=log)
        res["Instancia"] = nombre_inst
        resultados.append(res)
        _imprimir_resultado(res)

        print(f"\n[Gurobi] Modelo entero (MIP) — {nombre_inst}")
        log = os.path.join(DIR_LOGS, f"gurobi_{nombre_inst}_entero.log")
        res = resolver_gurobi(datos, es_relajado=False, log_filename=log)
        res["Instancia"] = nombre_inst
        resultados.append(res)
        _imprimir_resultado(res)

        # ── CPLEX ───────────────────────────────────────────────────────────
        print(f"\n[CPLEX]  Relajación lineal continua — {nombre_inst}")
        log = os.path.join(DIR_LOGS, f"cplex_{nombre_inst}_relajado.log")
        res = resolver_cplex(datos, es_relajado=True, log_filename=log)
        res["Instancia"] = nombre_inst
        resultados.append(res)
        _imprimir_resultado(res)

        print(f"\n[CPLEX]  Modelo entero (MIP) — {nombre_inst}")
        log = os.path.join(DIR_LOGS, f"cplex_{nombre_inst}_entero.log")
        res = resolver_cplex(datos, es_relajado=False, log_filename=log)
        res["Instancia"] = nombre_inst
        resultados.append(res)
        _imprimir_resultado(res)

    # ── Exportar resultados ──────────────────────────────────────────────────
    df = pd.DataFrame(resultados)[COLUMNAS]

    print(f"\n{'='*60}")
    print("  RESULTADOS CONSOLIDADOS")
    print(f"{'='*60}")
    print(df.to_string(index=False))

    df.to_csv(CSV_SALIDA, index=False)
    print(f"\nResultados guardados en: {CSV_SALIDA}")
    print(f"Logs guardados en:       {DIR_LOGS}/")


def _imprimir_resultado(res):
    """Imprime en consola un resumen de una corrida."""
    obj = f"{res['ObjVal']:.4f}" if res["ObjVal"] is not None else "N/A"
    gap = f"{res['Gap']:.2f}%" if res["Gap"] else "—"
    print(f"  Status: {res['Status']}  |  ObjVal: {obj}  |  "
          f"Tiempo: {res['Tiempo']:.2f}s  |  Nodos: {res['Nodos']}  |  Gap: {gap}")


if __name__ == "__main__":
    ejecutar_benchmark()
