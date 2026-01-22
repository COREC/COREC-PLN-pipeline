# -*- coding: utf-8 -*-

"""
1) Requisitos: Python 3.10+ (pandas)
2) Edita CONFIG:
   - CSV_BASE: ruta del CSV de frecuencias (analisis_de_frecuencias_def.csv)
   - OUT_DIR: carpeta de salida (CSVs por lengua + global)
   - K: nº de entrevistas prototípicas por lengua
3) Ejecuta:
   python 06_COREC_seleccion_muestra_prototipica.py
"""

import os
import pandas as pd

# --- Colab opcional ---
try:
    from google.colab import drive  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False


# =========================
# CONFIG (EDITAR AQUÍ)
# =========================
# --- LOCAL (por defecto; ejecutando desde la raíz del repo COREC) ---
CSV_BASE = "Frecuencias_basicas/analisis_de_frecuencias_def.csv"
OUT_DIR  = "Muestras_prototipicas/muestras_por_lengua"
K = 5

# --- COLAB (opcional; carpeta COREC subida a MyDrive) ---
if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    CSV_BASE = f"{REPO_ROOT}/Frecuencias_basicas/analisis_de_frecuencias_def_test.csv"
    OUT_DIR  = f"{REPO_ROOT}/Muestras_prototipicas/muestras_por_lengua_test"

# --- Si quieres montar Drive, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")
# =========================

# Crear carpeta de salida si no existe
os.makedirs(OUT_DIR, exist_ok=True)

# ---------- 1) Cargar el CSV base COMPLETO ----------
df_base = pd.read_csv(CSV_BASE, delimiter=";", encoding="utf-8")


# Lenguas a procesar
lenguas = df_base["lengua_contacto"].dropna().unique()
print("Lenguas que se van a procesar:", lenguas)

selecciones = []

for LENGUA_OBJETIVO in lenguas:
    print(f"\n=== Procesando lengua {LENGUA_OBJETIVO} ===")

    # ---------- 2) Filtrar esta lengua ----------
    df_lang = df_base[df_base["lengua_contacto"] == LENGUA_OBJETIVO].copy()
    if df_lang.empty:
        print("  (Sin datos, se salta)")
        continue

    # ---------- 3) Conversiones a RATIOS ----------
    df_lang["ratio_entrevistado"] = df_lang["prop_entrevistado"]
    df_lang["ratio_types"]       = df_lang["types_total"] / df_lang["tokens_totales"]
    df_lang["ratio_freq_2_5"]    = df_lang["freq_2_5"] / df_lang["types_total"]
    df_lang["ratio_ruido"]       = df_lang["marcas_ruido"] / df_lang["tokens_totales"]

    df = df_lang.copy()

    # ---------- 4) Distancia Manhattan a la mediana ----------
    metricas = [
        "ratio_entrevistado",
        "ratio_types",
        "ratio_freq_2_5",
    ]

    distancias = []
    for m in metricas:
        distancias.append((df[m] - df[m].median()).abs())

    df["dist_total"] = sum(distancias)

    # Penalización por ruido
    df["dist_total"] += df["ratio_ruido"]

    # ---------- 5) Ordenar y elegir prototipos ----------
    df_sorted = df.sort_values("dist_total")
    df_sel = df_sorted.head(K).copy()
    df_sel["k_orden"] = range(1, len(df_sel) + 1)

    # Guardar selección de esta lengua
    selecciones.append(df_sel)

    lang_code_clean = str(LENGUA_OBJETIVO).lstrip("'")
    out_csv_lang = os.path.join(OUT_DIR, f"seleccion_{lang_code_clean}.csv")
    df_sel.to_csv(out_csv_lang, sep=";", index=False, encoding="utf-8")

    print(f"  → Guardado CSV: {out_csv_lang}")
    print(f"  → Entrevistas seleccionadas: {len(df_sel)}")

# ---------- 6) CSV global con TODAS las lenguas ----------
if selecciones:
    df_corpus_oro = pd.concat(selecciones, ignore_index=True)
    out_global = os.path.join(OUT_DIR, "muestra_prototipica_global.csv")
    df_corpus_oro.to_csv(out_global, sep=";", index=False, encoding="utf-8")
    print("\nMuestra_global guardado en:", out_global)
else:
    print("\nNo se generaron selecciones.")
