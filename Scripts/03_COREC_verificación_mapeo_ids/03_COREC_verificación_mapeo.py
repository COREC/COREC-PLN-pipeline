# -*- coding: utf-8 -*-

"""
1) Requisitos: Python 3.10+ y pandas ->  pip install pandas
2) Edita CONFIG:
   - BASE_REN_DIR: ruta a la carpeta Ren o donde estén los .txt renombrados
   - CSV_PATH: ruta a ids.csv (separador ;)
   - BASE_ORIGINAL y BASE_REN_ROOT: raíces para validación cruzada
3) Ejecuta:
   python 03_verificacion_mapeo_ids.py
"""

from pathlib import Path
import pandas as pd
import unicodedata

# --- Colab opcional ---
try:
    from google.colab import drive  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False


# =========================
# CONFIG (EDITAR AQUÍ)
# =========================
# --- LOCAL (por defecto; rutas relativas al repositorio del COREC) ---
BASE_REN_DIR   = Path("Corpus/TXT/Ren")
CSV_PATH       = Path("Metadatos/Control/ids.csv")
BASE_ORIGINAL  = Path("Corpus/TXT/Original")
BASE_REN_ROOT  = Path("Corpus/TXT/Ren")

# --- COLAB (opcional; solo si estás en Colab) ---
if EN_COLAB:
    REPO_ROOT = Path("/content/drive/MyDrive/COREC")

    BASE_REN_DIR   = REPO_ROOT / "Corpus/TXT/Ren"
    CSV_PATH       = REPO_ROOT / "Metadatos/Control/ids.csv"
    BASE_ORIGINAL  = REPO_ROOT / "Corpus/TXT/Original"
    BASE_REN_ROOT  = REPO_ROOT / "Corpus/TXT/Ren"
# =========================


# --- Montaje de Drive, si estás en Colab ---
# if EN_COLAB:
#     drive.mount("/content/drive")


# ============================================================
# Funciones
# ============================================================
def normalizar(s: str) -> str:
    s = s.strip()
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))  
    s = s.lower().replace(" ", "").replace("_", "")
    return s

def clean_line(line: str) -> str:
    line = unicodedata.normalize("NFKD", line).strip().lower()
    return "".join(c for c in line if not unicodedata.combining(c))

def id_final(path: Path) -> str:
    return path.stem.split("_")[-1][-2:]

def lenguas_dict(path: Path):
    d = {}
    for child in path.iterdir():
        if child.is_dir():
            first = child.name.split("_")[0]
            if first.isdigit():
                d[int(first)] = child
    return d

def strip_ren(name: str) -> str:
    return name[4:] if name.startswith("Ren_") else name

def emparejar_subcarpeta(sub_o: Path, ren_subs):
    base = sub_o.name.lower()
    candidatos = []
    for d in ren_subs:
        nombre_r = strip_ren(d.name).lower()
        if base in nombre_r or nombre_r in base:
            candidatos.append(d)
    if not candidatos:
        return None
    if len(candidatos) == 1:
        return candidatos[0]
    candidatos.sort(key=lambda d: len(strip_ren(d.name)), reverse=True)
    return candidatos[0]


# ============================================================
# BLOQUE 1: CSV vs REN
# ============================================================
print(f"--- INICIO: Comprobando CSV contra carpeta REN ---")
print(f"CSV: {CSV_PATH}")
print(f"REN: {BASE_REN_DIR}")

if (not CSV_PATH.exists()) or (not BASE_REN_DIR.exists()):
    print("ERROR: No se encuentran las rutas definidas en CONFIG. Edita el script.")
else:
    df = pd.read_csv(CSV_PATH, sep=";")
    df["id"] = df["id"].astype(str).str.strip()
    df["Parte del nombre"] = df["Parte del nombre"].astype(str).str.strip()

    id_to_paths = {}
    for f in BASE_REN_DIR.rglob("*.txt"):
        stem = f.stem.strip()
        rel_path = f.relative_to(BASE_REN_DIR)
        id_to_paths.setdefault(stem, []).append(str(rel_path))

    resultados = []
    for _, row in df.iterrows():
        id_ = row["id"]
        parte = row["Parte del nombre"]
        paths = id_to_paths.get(id_, [])

        if not paths:
            resultados.append((id_, parte, "", "SIN_ARCHIVO"))
            continue

        parte_norm = normalizar(parte)
        estados_paths = []

        for r in paths:
            ruta_norm = normalizar(r)
            if parte_norm and parte_norm in ruta_norm:
                estados_paths.append((r, "OK_EN_ESTA_CARPETA"))
            else:
                estados_paths.append((r, "CARPETA_INCORRECTA"))

        if any(e == "OK_EN_ESTA_CARPETA" for _, e in estados_paths):
            if sum(1 for _, e in estados_paths if e == "OK_EN_ESTA_CARPETA") > 1:
                estado_global = "DUPLICADO_EN_VARIAS_CARPETAS_CORRECTAS"
            else:
                estado_global = "OK"
        else:
            estado_global = "EN_CARPETA_INCORRECTA"

        rutas_str = " | ".join(f"{r} [{e}]" for r, e in estados_paths)
        resultados.append((id_, parte, rutas_str, estado_global))

    res_df = pd.DataFrame(
        resultados,
        columns=["id", "Parte del nombre", "rutas_encontradas", "estado"]
    )

    print("\nRESUMEN DE ESTADOS:")
    print(res_df["estado"].value_counts())

    print("\nEjemplos con problema:")
    print(res_df[res_df["estado"] != "OK"].head(20))

    # SOBRANTES / FALTANTES (idéntico)
    ids_fs = set(id_to_paths.keys())
    ids_csv = set(df["id"])

    sobran = sorted(ids_fs - ids_csv)
    faltan = sorted(ids_csv - ids_fs)

    print("\n===== ARCHIVOS SOBRANTES (no están en el CSV) =====")
    if sobran:
        for x in sobran:
            print(" ❌", x)
    else:
        print(" ✓ No hay archivos sobrantes")

    print("\n===== ARCHIVOS DEL CSV QUE NO EXISTEN EN DRIVE (ya detectados) =====")
    if faltan:
        for x in faltan:
            print(" ❌", x)
    else:
        print(" ✓ Todos los del CSV existen correctamente")


# ============================================================
# BLOQUE 2: Validación cruzada ORIGINAL vs REN
# ============================================================
print(f"\n--- INICIO: Validación Cruzada (Estructura y Contenido) ---")

if (not BASE_ORIGINAL.exists()) or (not BASE_REN_ROOT.exists()):
    print("⚠ Saltando validación cruzada: Rutas Original/Ren no encontradas/incorrectas.")
else:
    orig_langs = lenguas_dict(BASE_ORIGINAL)
    ren_langs  = lenguas_dict(BASE_REN_ROOT)

    mismatches = []

    for idx in sorted(set(orig_langs.keys()) | set(ren_langs.keys())):
        orig_lang = orig_langs.get(idx)
        ren_lang  = ren_langs.get(idx)

        if orig_lang is None:
            mismatches.append((f"Lengua {idx}", "Sólo en REN", ren_lang.name))
            continue
        if ren_lang is None:
            mismatches.append((orig_lang.name, "Sólo en ORIGINAL (no hay carpeta en REN)"))
            continue

        orig_subs = [d for d in orig_lang.iterdir() if d.is_dir()]
        ren_subs  = [d for d in ren_lang.iterdir() if d.is_dir()]

        if not orig_subs and not ren_subs:
            orig_subs = [orig_lang]
            ren_subs  = [ren_lang]

        for sub_o in orig_subs:
            sub_r = emparejar_subcarpeta(sub_o, ren_subs)

            if sub_r is None:
                mismatches.append((
                    orig_lang.name,
                    f"Subcarpeta de ORIGINAL sin par en REN (por nombre parcial): {sub_o.name}"
                ))
                continue

            orig_files = list(sub_o.glob("*.txt"))
            ren_files  = list(sub_r.glob("*.txt"))

            ids_o = {id_final(f): f for f in orig_files}
            ids_r = {id_final(f): f for f in ren_files}

            ids_orig = set(ids_o.keys())
            ids_ren  = set(ids_r.keys())

            solo_o = sorted(ids_orig - ids_ren)
            solo_r = sorted(ids_ren  - ids_orig)

            if solo_o or solo_r:
                mismatches.append((
                    orig_lang.name,
                    sub_o.name,
                    f"IDs distintos (extra en ORIGINAL: {len(solo_o)}, extra en REN: {len(solo_r)})"
                ))
                continue

            for ID in sorted(ids_orig):
                fo = ids_o[ID]
                fr = ids_r[ID]

                lo = clean_line(fo.open(encoding="utf8").readline())
                lr = clean_line(fr.open(encoding="utf8").readline())

                if lo != lr:
                    mismatches.append((
                        orig_lang.name, sub_o.name, fo.name, fr.name,
                        f"Primera línea distinta para ID {ID}"
                    ))

    print("\n===================== RESULTADO FINAL =====================\n")

    if mismatches:
        print(f"Hay {len(mismatches)} incidencias detectadas:\n")
        for m in mismatches:
            print(m)
    else:
        print("TODO CORRECTO: Coincidencia 1:1 PERFECTA por lengua, subcarpeta, ID y contenido (1ª línea).")
