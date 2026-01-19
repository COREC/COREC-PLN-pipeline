# -*- coding: utf-8 -*-

"""
1) Requisitos: Python 3.10+ 
2) Edita CONFIG:
   - ROOT_IN: carpeta de entrada (Ren_limpio_fase_0)
   - CSV_OUT: ruta del CSV de salida
3) Ejecuta:
   python 05_COREC_analisis_frecuencias.py
"""

import os, re, csv
from collections import Counter

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
ROOT_IN = "Corpus/TXT/Ren_limpio_fase_0"
CSV_OUT = "Frecuencias_basicas/analisis_de_frecuencias_def.csv"

# --- COLAB (opcional; carpeta COREC subida a MyDrive) ---
if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    ROOT_IN = f"{REPO_ROOT}/Corpus/TXT/Ren_limpio_fase_0"
    CSV_OUT = f"{REPO_ROOT}/Frecuencias_basicas/analisis_de_frecuencias_def_test.csv"

# --- Si quieres montar Drive, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")

# -----------------------------------------------
#   PATRONES
# -----------------------------------------------
# Etiquetas de turno: E, I, INF, ENT, con o sin número, y combinadas con "/"
TAG_LABEL = r'(?:INF|ENT|E|I|C)(?:\d+)?'
TAG_SEQ   = rf'(?:{TAG_LABEL}(?:/{TAG_LABEL})*)'
TAG_TURN  = re.compile(rf'^\s*({TAG_SEQ})\s*:?\s*(.*)$')

# Marcas prosódicas que NO son tokens: /, //, ///
PROSODIC = re.compile(r'^/{1,3}$')

# Para dividir en partes: texto normal vs [ ], ( ), < >
BRACKET_SPLIT = re.compile(r'(\[[^\]]*\]|\([^)]*\)|<[^>]*>)')

# Limpieza de ":" en memoria (no en archivo)
# quita ":" al inicio, al final, o en medio de palabra (pe:ine -> peine)
REMOVE_COLON_IN_TOKEN = re.compile(r'^:|:$|(?<=\w):(?=\w)')

# Token normal (solo letras, incluidos acentos)
VALID_TOKEN = re.compile(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ]+$')


def process_file(path):
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    tokens_inf = []
    tokens_ent = []
    curr_speaker = None  # 'INF' o 'ENT'

    marcas_ruido = 0
    marcas_aclaracion = 0

    for line in lines:
        # 1 Detectar etiqueta de turno
        m = TAG_TURN.match(line)
        if m:
            tag = m.group(1).upper()  # E, E1/E2, I, INF, ENT...
            # Solo para decidir quién habla; NO es token
            if tag.startswith("I") or tag.startswith("INF") or tag.startswith("C"):
                curr_speaker = "INF"
            else:
                curr_speaker = "ENT"
            text = m.group(2)
        else:
            text = line

        # Si todavía no sabemos quién habla, no contamos tokens
        if curr_speaker is None:
            continue

        # 2 Dividir en segmentos: fuera y dentro de corchetes/paréntesis/angulares
        parts = BRACKET_SPLIT.split(text)

        for part in parts:
            if not part:
                continue

            # Caso A: parte es una marca [ ... ] / ( ... ) / < ... >
            if part[0] in "[(<" and part[-1] in "])>":
                inner = part[1:-1].strip()
                if not inner:
                    continue

                # Ruido / ininteligible si empieza por IN (cualquier mayús/minús)
                if inner.upper().startswith("IN"):
                    marcas_ruido += 1
                    # NO se cuenta como token
                else:
                    # Aclaración (corrección, glosa, etc.)
                    marcas_aclaracion += 1
                    # NO se cuenta como token
                continue

            # Caso B: parte es texto normal (fuera de corchetes)
            raw_tokens = [t for t in part.split() if t.strip()]

            for tok in raw_tokens:
                #  1) El ":" NUNCA es token; si va pegado a palabra lo limpiamos en memoria
                tok = REMOVE_COLON_IN_TOKEN.sub("", tok)
                if not tok:
                    continue

                #  2) Saltar marcas prosódicas /, //, ///
                if PROSODIC.fullmatch(tok):
                    continue

                #  3) Saltar etiquetas de turno que hayan quedado sueltas
                if re.fullmatch(TAG_SEQ, tok, flags=re.IGNORECASE):
                    continue

                #  4) Quitar puntuación lateral (.,;!?…)
                tok_clean = tok.strip(".,;:!?¡¿\"'")
                if not tok_clean:
                    continue

                #  5) Tratar los guiones: guion NO es token,
                #     pero la palabra con la que va SÍ.
                #     bue-no -> bueno ; cho- -> cho ; -cho -> cho ; marca-o -> marcao
                tok_clean = tok_clean.replace("-", "")
                if not tok_clean:
                    continue

                #  6) Ver si es una palabra alfabética válida
                if not VALID_TOKEN.fullmatch(tok_clean):
                    continue
                if tok_clean.lower() in {"tl", "sbx", "r"}:
                    continue

                #  7) Normalizar SOLO para conteos (no toca el archivo original)
                tok_norm = tok_clean.lower()

                #  8) Asignar al hablante correspondiente
                if curr_speaker == "INF":
                    tokens_inf.append(tok_norm)
                else:
                    tokens_ent.append(tok_norm)

    # -------------------------------
    #   Métricas por entrevista
    # -------------------------------
    tokens_totales = len(tokens_inf) + len(tokens_ent)
    if tokens_totales > 0:
        porc_inf = round(len(tokens_inf) / tokens_totales, 3)
    else:
        porc_inf = 0.0

    # Frecuencias léxicas
    freqs = Counter(tokens_inf + tokens_ent)
    types_total = len(freqs)
    hapax = sum(1 for _, f in freqs.items() if f == 1)
    freq_2_5 = sum(1 for _, f in freqs.items() if 2 <= f <= 5)
    pct_2_5 = round(freq_2_5 / types_total * 100, 2) if types_total > 0 else 0.0

    return (
        tokens_totales,
        len(tokens_inf),
        len(tokens_ent),
        porc_inf,
        types_total,
        hapax,
        freq_2_5,
        pct_2_5,
        marcas_ruido,
        marcas_aclaracion,
    )


# -----------------------------------------------
#   Crear el CSV de salida
# -----------------------------------------------
fields = [
    "id_muestra",
    "lengua_contacto",
    "pais_region",
    "tokens_totales",
    "tokens_entrevistado",
    "tokens_entrevistador",
    "porc_entrevistado",
    "types_total",
    "hapax",
    "freq_2_5",
    "%_freq_2_5",
    "marcas_ruido",
    "marcas_aclaracion",
]

with open(CSV_OUT, "w", encoding="utf-8", newline="") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(fields)

    for dp, _, files in os.walk(ROOT_IN):
        for file in files:
            if not file.lower().endswith(".txt"):
                continue

            id_muestra = file[:-4]  # sin .txt

            # id_muestra = codLengua_codPais_codRegion_...
            partes = id_muestra.split("_")
            codLengua = partes[0] if len(partes) > 0 else ""
            codPais   = partes[1] if len(partes) > 1 else ""

            path = os.path.join(dp, file)
            print("→ Procesando:", path)

            vals = process_file(path)

          #  Proteger identificadores como texto para que Excel NO los modifique
            id_txt = "'" + id_muestra
            lang_txt = "'" + codLengua
            pais_txt = "'" + codPais

            row = [id_txt, lang_txt, pais_txt] + list(vals)
            writer.writerow(row)



print("analisis de frecuencias_def. CSV generado en:", CSV_OUT)

