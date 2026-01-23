# -*- coding: utf-8 -*-

"""
1) Requisitos: Python 3.10+
   - spaCy + modelo español es_core_news_lg
2) Edita CONFIG:
   - ROOT_IN: carpeta de entrada (Ren_limpio_fase_0)
   - ROOT_OUT: carpeta de salida (segmentación discursiva)
   - MIN_WORDS_FOR_SLASH_CUT, etc.
3) Ejecuta:
   python 07_COREC_segmentacion_discursiva.py
"""

import os
import re
from pathlib import Path

# --- Colab opcional ---
try:
    from google.colab import drive  
    EN_COLAB = True
except Exception:
    EN_COLAB = False

# ===========================================================
# spaCy 
# ===========================================================

import spacy
nlp = spacy.load("es_core_news_lg")
print("spaCy cargado:", nlp.meta["name"])

# ===========================================================
# CONFIG 
# ===========================================================
# --- LOCAL---
ROOT_IN  = "Corpus/TXT/Ren_limpio_fase_0"
ROOT_OUT = "Preprocesamiento_linguistico/1_Textos_segmentacion_discursiva"

# --- COLAB (opcional; carpeta COREC subida a MyDrive) ---

if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    ROOT_IN  = f"{REPO_ROOT}/Corpus/TXT/Ren_limpio_fase_0"
    ROOT_OUT = f"{REPO_ROOT}/Preprocesamiento_linguistico/1_Textos_segmentacion_discursiva_test"

# --- Si quieres montar Drive, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")
# ===========================================================


MIN_WORDS_FOR_SLASH_CUT = 8

NEXOS = {
    "y", "pero", "porque", "entonces", "por", "por ejemplo",
    "ya sea", "así", "aunque", "sino", "que"
}

PATRONES_CIERRE = [
    r"\beso fue\b",
    r"\beso sería\b",
    r"\bme di cuenta\b",
    r"\bme sorprendió\b",
    r"\bpor eso\b",
    r"\bno sé\b",
]

TRAIL_PUNCT = re.compile(r"[.,;:¡!¿?\)\]\}]+$")
RE_CIERRE = re.compile("|".join(PATRONES_CIERRE), flags=re.IGNORECASE)

TAG_LABEL = r"(?:INF|ENT|E|I|C)(?:\d+)?"
TAG_SEQ   = rf"(?:{TAG_LABEL}(?:/{TAG_LABEL})*)"
TAG_TURN  = re.compile(rf"^\s*({TAG_SEQ})\s*:?\s*(.*)$")

PREVIEW_N = 5

# ===========================================================
# Limpieza para spaCy
# ===========================================================
def para_analisis_spacy(texto: str) -> str:
    texto = re.sub(r"\b[A-Z]+\d*:\s*", " ", texto)
    texto = re.sub(r"<~.*?>", " ", texto)
    texto = re.sub(r"^[.\s\t]+", "", texto)
    texto = re.sub(r"^[A-Z]{1,3}\s+", "", texto)
    texto = re.sub(r"[:\-]", "", texto)
    return re.sub(r"\s+", " ", texto).strip()


# ===========================================================
# CONDICIONES SINTÁCTICAS (x1, x2, x4)
# ===========================================================

def normaliza_barras(texto: str) -> str:
    texto = re.sub(r"\s*/{1,3}\s*", " / ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def tiene_verbo_finito(texto: str) -> bool:
    doc = nlp(para_analisis_spacy(texto))
    for tok in doc:
        if tok.pos_ in {"VERB", "AUX"}:
            if "Fin" in tok.morph.get("VerbForm"):
                return True
            if tok.morph.get("Mood") or tok.morph.get("Tense"):
                return True
    return False

def termina_en_nexos(texto: str) -> bool:
    t = texto.lower().strip()
    t = TRAIL_PUNCT.sub("", t)
    for c in NEXOS:
        if t.endswith(c):
            return True
    return False

def es_cierre_evaluativo(texto: str) -> bool:
    return bool(RE_CIERRE.search(texto))

# ===========================================================
# BLOQUEO ESTRUCTURAL (x5)
# ===========================================================

def es_bloqueo_x5(texto_izq: str, toks, i_next, max_look=6) -> bool:
    j = i_next
    while j < len(toks) and toks[j] == "/":
        j += 1
    if j >= len(toks):
        return False

    # DERECHA (prospectivo)
    ventana_tokens = toks[j:j+max_look]
    texto_ventana = " ".join(ventana_tokens).lower()
    doc = nlp(para_analisis_spacy(texto_ventana))
    if len(doc) == 0:
        return False

    # --- CASO A: a/de/para + infinitivo ---
    if doc[0].text.lower() in {"a", "de", "para"}:
        for tok in doc:
            if tok.pos_ in {"VERB", "AUX"} and "Inf" in tok.morph.get("VerbForm"):
                return True

    # --- CASO B: relativos/completivas ---
    if doc[0].lemma_ in {"que", "quien", "cual", "cuyo", "donde"}:
        if doc[0].pos_ in {"PRON", "SCONJ", "ADV"}:
            return True

    if len(doc) > 1:
        if doc[0].pos_ in {"DET", "PRON"} and doc[1].lemma_ == "que":
            return True

    if len(doc) > 1:
        if doc[0].pos_ == "ADP" and doc[1].lemma_ in {"donde", "que", "quien", "cual"}:
            if doc[1].pos_ in {"PRON", "SCONJ", "ADV"}:
                return True

    # --- CASO C: copulativo a la IZQUIERDA LOCAL ---
    doc_izq = nlp(para_analisis_spacy(texto_izq))

    ultimo_verbo = None
    for tok in reversed([t for t in doc_izq if not t.is_punct]):
        if tok.pos_ in {"VERB", "AUX"}:
            ultimo_verbo = tok
            break

    if ultimo_verbo is not None and ultimo_verbo.lemma_ in {"ser", "estar", "parecer"}:
        primer_der = None
        for t in doc:
            if not t.is_punct:
                primer_der = t
                break

        if primer_der is not None and primer_der.pos_ in {"ADJ", "NOUN", "PROPN"}:
            return True

    return False


# ===========================================================
# SEGMENTACIÓN (Aplica f(xi) = ((x1 v x4) ^ x2 ^ x3) ^ !x5)
# ===========================================================
def segmentar_turno(texto_turno: str):
    t = normaliza_barras(texto_turno)
    if not t:
        return []

    toks = t.split()
    oraciones, actual = [], []

    for i, tok in enumerate(toks):

        if tok == "/":
            sent = " ".join(actual).strip()
            if not sent:
                continue

            # --- CÁLCULO DE RASGOS 
            x1_verb   = tiene_verbo_finito(sent)
            x2_no_nexo = not termina_en_nexos(sent)
            x3_long   = (len(sent.split()) >= MIN_WORDS_FOR_SLASH_CUT)
            x4_pragm  = es_cierre_evaluativo(sent)
            x5_block  = es_bloqueo_x5(sent, toks, i+1)


            # --- FUNCIÓN DE DECISIÓN f(xi) ---
            if ((x1_verb or x4_pragm) and x2_no_nexo and x3_long) and not x5_block:
                oraciones.append(sent)
                actual = []
            else:
                continue

        else:
            actual.append(tok)

    sent = " ".join(actual).strip()
    if sent:
        oraciones.append(sent)

    
    oraciones = [re.sub(r"\s*,\s*,\s*", ", ", s) for s in oraciones]
    oraciones = [re.sub(r"\s+", " ", s).strip() for s in oraciones]

    return [s.strip() for s in oraciones if s.strip()]

# ===========================================================
# PROCESADO
# ===========================================================
def procesar_txt(path_in: str, path_out: str):
    with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
        lines = [ln.rstrip("\n") for ln in f]

    salida = []
    preview = []
    current_speaker = None
    buffer = []

    def flush():
        nonlocal buffer, current_speaker
        if current_speaker and buffer:
            content = " ".join(buffer).strip()
            sents = segmentar_turno(content)
            for s in sents:
                linea = f"{current_speaker}: {s}"
                salida.append(linea)
                preview.append(linea)
        buffer = []

    for ln in lines:
        if not ln.strip(): continue
        m = TAG_TURN.match(ln)
        if m:
            flush()
            current_speaker = m.group(1)
            content = m.group(2).strip()
            buffer = [content] if content else []
        else:
            if current_speaker:
                buffer.append(ln.strip())
    flush()

    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    with open(path_out, "w", encoding="utf-8") as f:
        for s in salida:
            f.write(s + "\n")
    return preview

# ============
# MAIN 
# ============
print("ROOT_IN existe?:", os.path.exists(ROOT_IN))
all_txt = []
for dp, _, files in os.walk(ROOT_IN):
    for name in files:
        if name.lower().endswith(".txt"):
            all_txt.append(os.path.join(dp, name))

print("TXT encontrados:", len(all_txt))

total = 0
for src in all_txt:
    dp = os.path.dirname(src)
    rel = os.path.relpath(dp, ROOT_IN)
    out_dir = os.path.join(ROOT_OUT, rel)
    dst = os.path.join(out_dir, Path(src).name.replace(".txt", "_seg.txt"))

    print("\n==============================")
    print("Archivo:", src)
    preview = procesar_txt(src, dst)

    print("\nVista previa:\n")
    for i, s in enumerate(preview[:PREVIEW_N], 1):
        print(f"{i:02d}: {s}")
    total += 1

print("\n Segmentación finalizada. Total:", total)
