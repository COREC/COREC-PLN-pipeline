# -*- coding: utf-8 -*-

"""
COREC II — Normalización (Normas 7, 5, 1, 4, 6, 3, 8, 10)

Descripción
Este script aplica la fase de Normalización I a entrevistas ya segmentadas discursivamente.
No modifica las etiquetas de turno (I1:, E1:, etc.). Genera:
- TXT normalizados (Salida_TXT_normas_1)
- Log CSV de trazabilidad (Log_normas_1.csv)

Entrada
Carpeta: Preprocesamiento_linguistico/1_Textos_segmentacion_discursiva/
Archivos: <ID_compuesto>_seg.txt
Codificación: UTF-8

Salida
Carpeta: Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1/
Archivos: <ID_compuesto>_seg_normas_1.txt
Log: Preprocesamiento_linguistico/3_Logs/Log_normas_1/Log_normas_1.csv
Separador log: ;
Codificación log: UTF-8-SIG

Requisitos
- Python 3.10+
- Hunspell + diccionarios de español (REQUERIDO para Norma 10)
  En Colab:
    apt-get install -y hunspell hunspell-es libhunspell-dev
    pip install hunspell
  En local (Linux):
    instala hunspell + diccionarios es_ES del sistema y el wrapper de Python

Uso
Desde la raíz del repositorio:
python 08_COREC_normas_preprocesamiento.py

En Colab (opcional):
- Monta Drive (drive.mount)
- Ajusta REPO_ROOT (ver CONFIG)
- Ejecuta:
!python 08_COREC_normas_preprocesamiento.py
"""

import re
import csv
import unicodedata
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional

# --- Colab opcional ---
try:
    from google.colab import drive  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False


# =========================
# CONFIG (EDITAR AQUÍ)
# =========================
# --- LOCAL (desde raíz del repo COREC) ---
ROOT_IN = "Preprocesamiento_linguistico/1_Textos_segmentacion_discursiva"
OUT_DIR = "Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1"
OUT_CSV = "Preprocesamiento_linguistico/3_Logs/Log_normas_1/Log_normas_1.csv"

# --- COLAB (opcional; NO sobreescribir) ---
if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    ROOT_IN = f"{REPO_ROOT}/{ROOT_IN}"
    OUT_DIR = f"{REPO_ROOT}/Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1_test"
    OUT_CSV = f"{REPO_ROOT}/Preprocesamiento_linguistico/3_Logs/Log_normas_1/Log_normas_1_test.csv"

# --- Si quieres montar Drive, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")

Path(OUT_DIR).mkdir(parents=True, exist_ok=True)
Path(OUT_CSV).parent.mkdir(parents=True, exist_ok=True)


# ===========================================================
# Hunspell — REQUERIDO (Norma 10)
# ===========================================================
HUN = None
try:
    from hunspell import HunSpell  # type: ignore
    CANDIDATES = [
        ("/usr/share/hunspell/es_ES.dic", "/usr/share/hunspell/es_ES.aff"),
        ("/usr/share/hunspell/es_ANY.dic", "/usr/share/hunspell/es_ANY.aff"),
        ("/usr/share/myspell/es_ES.dic", "/usr/share/myspell/es_ES.aff"),
    ]
    for dic_path, aff_path in CANDIDATES:
        if Path(dic_path).exists() and Path(aff_path).exists():
            HUN = HunSpell(dic_path, aff_path)
            break
except Exception:
    HUN = None

if HUN is None:
    raise RuntimeError(
        "Hunspell es REQUERIDO para Norma 10 y no se encontró dic/aff.\n"
        "En Colab instala:\n"
        "  apt-get install -y hunspell hunspell-es libhunspell-dev\n"
        "  pip install hunspell\n"
        "En local: instala hunspell + diccionarios de español del sistema."
    )

def hun_ok(word: str) -> bool:
    w = word.strip()
    if not w:
        return False
    try:
        return bool(HUN.spell(w))
    except Exception:
        return False


# ===========================================================
# 1 UD = 1 línea etiquetada  (captura label + resto)
# ===========================================================
LABEL_RE = re.compile(
    r"""^\s*
    (?P<label>(?:INF|ENT|E|I)(?:[0-9]+|(?:\.[A-Za-z0-9]+))*)
    \s*:\s*
    (?P<rest>.*)$
    """,
    flags=re.VERBOSE
)

# Detecta bloques
BRACKET_BLOCK_RE = re.compile(r"\[[^\]]*\]")
BRACE_BLOCK_RE   = re.compile(r"\{[^}]*\}")
PAREN_BLOCK_RE   = re.compile(r"\([^)]*\)")

# Truncamiento
TRUNC_CORR_RE = re.compile(r"\b(?P<x>\w+)[-–—]\s*\[(?P<y>[^\]]+)\]", flags=re.UNICODE)

# Truncamiento aislado: X-  (solo si NO va seguida de [Y])
TRUNC_ALONE_RE = re.compile(
    r"\b(?P<x>\w+)[-–—](?=(?:\s|$|[.,;:!?¿¡]))(?!\s*\[)",
    flags=re.UNICODE
)

# Norma 4: token + [X]
LEXVAR_RE = re.compile(r"(?P<prev>\b\w+\b)\s*:?\s*\[(?P<br>[^\]]+)\]")


# Norma 8: repeticiones vocálicas
# A/I/U: 2+ -> 1
VOWEL_REPEAT_AIU_RE = re.compile(r"([AIUÁÍÚaiuáíú])\1+")
# E/O: 3+ -> 1  (permite ee/oo legítimos: creer, leer, etc.)
VOWEL_REPEAT_EO_RE  = re.compile(r"([EOÉÓeoéó])\1{2,}")

Y_REPEAT_RE     = re.compile(r"\b[yY]{2,}\b", flags=re.UNICODE)

# Norma 8b — consonantes repetidas al FINAL (2+), excepto ll/rr
CONS_FINAL_REPEAT_RE = re.compile(
    r"\b(?P<stem>\w*?)(?P<c>[BCDFGHJKLMNPQRSTVWXZÑbcdfghjklmnpqrstvwxzñ])(?P=c)+\b",
    flags=re.UNICODE
)

# ===========================================================
# PARALINGÜÍSTICO
# ===========================================================
# Tokens tipo risa: "jajaja", "jeje", "hahaha", etc. (sin corchetes)
RISA_TOKEN_RE = re.compile(
    r"(?iu)^j(?=(?:.*j){2,})(?=.*[aeiouáéíóúü])[jaeiouáéíóúü]{4,}$"
)


# ===========================================================
# Norma 6: lenguas (detección) -> placeholder L2
# ===========================================================
LANG_PLACEHOLDER: Dict[str, str] = {
    "kichwa": "KICHWA",
    "quichua": "QUICHUA",
    "quechua": "QUECHUA",
    "quechhua": "QUECHHUA",
    "otomi": "OTOMÍ",
    "otomí": "OTOMÍ",
    "tsotsil": "TSOTSIL",
    "euskera": "EUSKERA",
    "tepehuano": "TEPEHUANO",
    "guarani": "GUARANÍ",
    "guaraní": "GUARANÍ",
    "tzutujil": "TZUTUJIL",
    "portugues": "PORTUGUÉS",
    "portugués": "PORTUGUÉS",
    "andino colombiano": "ANDINO_COLOMBIANO",
    "asturiano": "ASTURIANO",
}

def _strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s)
        if unicodedata.category(c) != "Mn"
    )

def _norm_lang_key(s: str) -> str:
    return _strip_accents(s).lower()

LANG_KEYS = sorted({_norm_lang_key(k) for k in LANG_PLACEHOLDER.keys()}, key=len, reverse=True)

# ===========================================================
# LOG STRUCT
# ===========================================================
@dataclass
class LogRow:
    id_archivo: str
    id_ud: str
    linea_n: int
    hablante: str
    rol: str
    norma_id: int
    fenomeno: str
    forma_original: str
    forma_resultante: str
    accion: str
    contexto: str

def rol_from_label(label: str) -> str:
    lab = label.upper()
    if lab.startswith("E") or lab.startswith("ENT"):
        return "ENTREVISTADOR"
    return "INFORMANTE"

def iter_txt_files(root: str) -> List[Path]:
    rootp = Path(root)
    if rootp.is_file() and rootp.suffix.lower() == ".txt":
        return [rootp]
    return sorted([p for p in rootp.rglob("*.txt") if p.is_file()])

print("Regex + LogRow OK")

# ===========================================================
# UTILIDADES
# ===========================================================
def _clean_line_prefix(rest: str) -> str:
    # En Normas 1..11 (excepto 2) NO limpiamos prefijos.
    # La limpieza de ". TL", ". 1.", etc. la hará Norma 2 (tu script de dos puntos).
    return rest

def _squash_spaces(s: str) -> str:
    # Colapsa espacios múltiples creados por eliminaciones,
    # pero NO hace .strip() (no toca inicio/fin del texto).
    return re.sub(r"\s{2,}", " ", s)

# ---------------------------
# Norma 7 — Paréntesis (con detección L2 como Norma 6)
# Soporta anidamiento por iteración y limpia paréntesis sueltos
# ---------------------------
def norma7_parentesis(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    def repl(m: re.Match) -> str:
        fo = m.group(0)
        inner = fo[1:-1]  # sin ( )
        l2 = _detect_l2(inner)
        if l2:
            fr = f"⟦L2_{l2}⟧"
            events.append((fo, fr, "NORMA7_L2"))
            return fr
        else:
            events.append((fo, "", "NORMA7_APLICADA"))
            return ""

    out = text

    # 1) Iterar: elimina por capas hasta que no cambie
    while True:
        new_out = PAREN_BLOCK_RE.sub(repl, out)
        if new_out == out:
            break
        out = new_out

    # 2) Limpieza final: paréntesis sueltos (residuo de transcripción)
    if "(" in out or ")" in out:
        out = out.replace("(", "").replace(")", "")

    out = _squash_spaces(out)
    return out, events



# ---------------------------
# Norma 5 — < > fuera de [ ] y { }
# ---------------------------
def norma5_angulares_fuera(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []
    out_chars = []
    i = 0
    sq = 0
    cu = 0
    n = len(text)

    while i < n:
        ch = text[i]
        if ch == "[":
            sq += 1
            out_chars.append(ch)
            i += 1
            continue
        if ch == "]":
            sq = max(0, sq - 1)
            out_chars.append(ch)
            i += 1
            continue
        if ch == "{":
            cu += 1
            out_chars.append(ch)
            i += 1
            continue
        if ch == "}":
            cu = max(0, cu - 1)
            out_chars.append(ch)
            i += 1
            continue

        if ch == "<" and sq == 0 and cu == 0:
            j = i + 1
            while j < n and text[j] != ">":
                j += 1
            if j < n and text[j] == ">":
                fo = text[i:j+1]
                events.append((fo, "", "NORMA5_APLICADA"))
                i = j + 1
                continue
            # si no cierra, lo dejamos
        out_chars.append(ch)
        i += 1

    out = "".join(out_chars)
    out = _squash_spaces(out)
    return out, events

# ---------------------------
# Norma 1 — Truncamiento con guion
# ---------------------------
def norma1_truncamientos(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []
    out = text

    # (2) X- [Y]  -> Y
    def repl_corr(m: re.Match) -> str:
        y = m.group("y").strip()
        fo = m.group(0)
        events.append((fo, y, "NORMA1_CORRECCION"))
        return y

    out2 = TRUNC_CORR_RE.sub(repl_corr, out)

    # (1) X- aislado -> Ø
    def repl_alone(m: re.Match) -> str:
        fo = m.group(0)
        events.append((fo, "", "NORMA1_TRUNC_ELIMINADA"))
        return ""

    out3 = TRUNC_ALONE_RE.sub(repl_alone, out2)
    out3 = _squash_spaces(out3)
    return out3, events
# ---------------------------
# Norma 4 — Variantes léxicas con [X]
# (limpia < y ~ dentro del corchete)
# ---------------------------
def _letters_equiv(s: str) -> str:
    s = s.lower()

    # Normaliza tildes/diacríticos SOLO para comparar
    s = (s.replace("á", "a").replace("é", "e").replace("í", "i")
           .replace("ó", "o").replace("ú", "u").replace("ü", "u"))

    # Equivalencias
    s = s.replace("ll", "y")
    s = s.replace("i", "y")  # í->i->y
    s = s.replace("y", "y")

    # Solo letras (ya sin tildes)
    s = re.sub(r"[^a-zñ]+", "", s, flags=re.UNICODE)
    return s

def _has_common_bigram(a: str, b: str) -> bool:
    if len(a) < 2 or len(b) < 2:
        return False
    bigrams = {a[i:i+2] for i in range(len(a)-1)}
    for j in range(len(b)-1):
        if b[j:j+2] in bigrams:
            return True
    return False

def _similar_enough(prev_raw: str, br_raw: str) -> bool:
    a = _letters_equiv(prev_raw)
    b = _letters_equiv(br_raw)

    if not a or not b:
        return False

    # Tokens muy cortos (1–2 letras): basta 1 letra común
    if len(a) <= 2:
        return any(ch in b for ch in set(a))

    # Tokens normales (>=3): bigrama común
    return _has_common_bigram(a, b)

META_BLOCKS = {
    "risas", "risa", "carraspea", "tos", "tose", "silencio",
    "ruidos", "ruido", "música", "timbre", "n. de t.",
}

def _is_meta_bracket(br_clean: str) -> bool:
    s = br_clean.strip().lower()
    s = re.sub(r"\s+", " ", s)

    # 1) Caso directo: exactamente igual
    if s in META_BLOCKS:
        return True

    # 2) Caso típico: notas del transcriptor al inicio
    if s.startswith("n. de t."):
        return True

    # 3) Caso frase: contiene una de las claves meta como palabra
    # (evita falsos positivos tipo "contimbre" usando bordes de palabra)
    for kw in META_BLOCKS:
        if re.search(rf"\b{re.escape(kw)}\b", s):
            return True

    return False


def norma4_lexvar(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    def repl(m: re.Match) -> str:
        prev = m.group("prev")
        br_raw = m.group("br")
        br_clean = br_raw.replace("<", "").replace("~", "").strip()

        # Si es meta ([risas], etc.) NO aplicar Norma 4:
        # lo dejamos intacto para que lo elimine Norma 6.
        if _is_meta_bracket(br_clean):
            return m.group(0)


        if _similar_enough(prev, br_clean):
            fo = m.group(0)
            fr = br_clean
            events.append((fo, fr, "NORMA4_SUSTITUCION"))
            return fr


        return m.group(0)

    out = LEXVAR_RE.sub(repl, text)
    out = _squash_spaces(out)
    return out, events


# ---------------------------
# Norma 6 — [ ] y { } no léxicos + excepción L2
# + borrar risas SUELTAS fuera de [ ] y { }
# ---------------------------
def _detect_l2(content: str) -> Optional[str]:
    c = content.strip()
    c_norm = _norm_lang_key(c)
    for k in LANG_KEYS:
        if k and k in c_norm:
            for orig, up in LANG_PLACEHOLDER.items():
                if _norm_lang_key(orig) == k:
                    return up
            if k == "andino colombiano":
                return "ANDINO_COLOMBIANO"
            return k.upper()
    return None


def norma6_corchetes_llaves(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    # 0) spans de bloques para NO tocar nada dentro de [] o {}
    protected_spans = [(m.start(), m.end()) for m in BRACKET_BLOCK_RE.finditer(text)]
    protected_spans += [(m.start(), m.end()) for m in BRACE_BLOCK_RE.finditer(text)]

    def _is_protected(pos: int) -> bool:
        for a, b in protected_spans:
            if a <= pos < b:
                return True
        return False

    # 1) Fuera de corchetes/llaves: borrar risas sueltas tipo "jajaja"
    def repl_word(m: re.Match) -> str:
        if _is_protected(m.start()):
            return m.group(0)
        tok = m.group(0)
        if RISA_TOKEN_RE.match(tok):
            events.append((tok, "", "NORMA6_RISA_FUERA"))
            return ""
        return tok

    out = re.sub(r"\b\w+\b", repl_word, text, flags=re.UNICODE)

    # 2) Bloques [] y {} (como siempre): borrar salvo L2
    def handle_block(fo: str) -> str:
        inner = fo[1:-1]  # sin [] o {}
        l2 = _detect_l2(inner)
        if l2:
            fr = f"⟦L2_{l2}⟧"
            events.append((fo, fr, "NORMA6_L2"))
            return fr
        else:
            events.append((fo, "", "NORMA6_NO_LEXICO"))
            return ""

    out = BRACKET_BLOCK_RE.sub(lambda m: handle_block(m.group(0)), out)
    out = BRACE_BLOCK_RE.sub(lambda m: handle_block(m.group(0)), out)

    out = _squash_spaces(out)
    return out, events


# ===========================================================
# Norma 3 — puntos suspensivos (incluye ". . ." con espacios)
# ===========================================================
ELLIPSIS_RE = re.compile(r"(?:\.\s*){3,}|…", flags=re.UNICODE)

def norma3_puntos_susp(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    def repl(m: re.Match) -> str:
        fo = m.group(0)
        start, end = m.span()

        left_is_word  = (start > 0 and re.match(r"\w", text[start - 1]) is not None)
        right_is_word = (end < len(text) and re.match(r"\w", text[end]) is not None)

        # Si está entre dos caracteres de palabra: separar con espacio
        if left_is_word and right_is_word:
            events.append((fo, " ", "NORMA3_APLICADA"))
            return " "

        # Resto de casos: eliminar como antes
        events.append((fo, "", "NORMA3_APLICADA"))
        return ""

    out = ELLIPSIS_RE.sub(repl, text)
    out = _squash_spaces(out)
    return out, events

# ---------------------------
# Norma 8 — repeticiones vocálicas + Yyy -> y
# ---------------------------
def norma8_repeticiones(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    def repl_v(m: re.Match) -> str:
        fo = m.group(0)
        fr = m.group(1)
        events.append((fo, fr, "NORMA8_VOCAL"))
        return fr

    # antes: out = VOWEL_REPEAT_RE.sub(repl_v, text)
    out = VOWEL_REPEAT_AIU_RE.sub(repl_v, text)
    out = VOWEL_REPEAT_EO_RE.sub(repl_v, out)

    # NUEVO: consonantes finales repetidas (2+), excepto ll/rr
    def repl_c(m: re.Match) -> str:
        stem = m.group("stem")
        c = m.group("c")
        fo = m.group(0)

        # Excepciones: mantener "ll" y "rr" al final
        if (stem.lower().endswith("l") and c.lower() == "l") or (stem.lower().endswith("r") and c.lower() == "r"):
            return fo

        fr = stem + c
        events.append((fo, fr, "NORMA8_CONS_FINAL"))
        return fr

    out = CONS_FINAL_REPEAT_RE.sub(repl_c, out)

    def repl_y(m: re.Match) -> str:
        fo = m.group(0)
        fr = "y"
        events.append((fo, fr, "NORMA8_Y"))
        return fr

    out = Y_REPEAT_RE.sub(repl_y, out)
    out = _squash_spaces(out)
    return out, events


# ---------------------------
# Norma 10 — mayúsculas enfáticas
# ---------------------------
def _is_title_case(tok: str) -> bool:
    if len(tok) < 2:
        return False
    return tok[0].isupper() and tok[1:].islower()

def _is_allcaps(tok: str) -> bool:
    has_alpha = any(c.isalpha() for c in tok)
    return has_alpha and tok.isupper()

def norma10_mayus(text: str) -> Tuple[str, List[Tuple[str, str, str]]]:
    events = []

    def repl(m: re.Match) -> str:
        tok = m.group(0)

        if _is_title_case(tok):
            return tok

        if _is_allcaps(tok):
            low = tok.lower()

            if 2 <= len(tok) <= 10:
                if hun_ok(low):
                    events.append((tok, low, "NORMA10_BAJA"))
                    return low
                else:
                    return tok

            events.append((tok, low, "NORMA10_BAJA"))
            return low

        return tok

    out = re.sub(r"\b\w+\b", repl, text, flags=re.UNICODE)
    out = _squash_spaces(out)
    return out, events

print("Funciones de normas OK (sin limpiar prefijos)")

# ==================================================================
# APLICAR NORMAS (1) SIN TOCAR ETIQUETAS NI PREFIJOS
# ==================================================================

def apply_normas_sin_2_9_11(
    contexto_raw: str,      # <- RESTO TAL CUAL (incluye . TL, . 1., etc. si aparecen)
    id_archivo: str,
    id_ud: str,
    linea_n: int,
    hablante: str,
    rol: str,
    rows: List[LogRow],
) -> Optional[str]:
    """
    Aplica el orden:
      7, 5, 1, 4, 6, 3, 8, 10

    (Norma 2 se ejecuta en tu script de dos puntos.
     Norma 9 y Norma 11 se ejecutarán DESPUÉS de la Norma 2, fuera de este bloque.)

    Si el RESTO queda vacío, devuelve None (se elimina la línea completa).
    """
    text = contexto_raw  # <- NO limpiar prefijos aquí

    def add_events(norma_id: int, fenomeno: str, events: List[Tuple[str, str, str]]):
        for fo, fr, accion in events:
            rows.append(LogRow(
                id_archivo=id_archivo,
                id_ud=id_ud,
                linea_n=linea_n,
                hablante=hablante,
                rol=rol,
                norma_id=norma_id,
                fenomeno=fenomeno,
                forma_original=fo,
                forma_resultante=fr,
                accion=accion,
                contexto=contexto_raw
            ))

    # Norma 7
    text2, ev = norma7_parentesis(text)
    add_events(7, "PARENTESIS", ev)
    text = text2

    # Norma 5
    text2, ev = norma5_angulares_fuera(text)
    add_events(5, "COMILLAS_ANGULARES", ev)
    text = text2

    # Norma 1
    text2, ev = norma1_truncamientos(text)
    add_events(1, "TRUNCAMIENTO_GUION", ev)
    text = text2

    # Norma 4
    text2, ev = norma4_lexvar(text)
    add_events(4, "VARIANTE_LEXICA_CORCHETES", ev)
    text = text2

    # Norma 6
    text2, ev = norma6_corchetes_llaves(text)
    add_events(6, "NO_LEXICO_CORCHETES_LLAVES_L2", ev)
    text = text2

    # Norma 3
    text2, ev = norma3_puntos_susp(text)
    add_events(3, "PUNTOS_SUSPENSIVOS", ev)
    text = text2

    # Norma 8
    text2, ev = norma8_repeticiones(text)
    add_events(8, "REPETICION_VOCALICA", ev)
    text = text2

    # Norma 10
    text2, ev = norma10_mayus(text)
    add_events(10, "MAYUSCULAS_ENFATICAS", ev)
    text = text2

    # Si el RESTO queda vacío -> eliminar línea completa
    if not text.strip():
        rows.append(LogRow(
            id_archivo=id_archivo,
            id_ud=id_ud,
            linea_n=linea_n,
            hablante=hablante,
            rol=rol,
            norma_id=0,
            fenomeno="LINEA_VACIA",
            forma_original=contexto_raw,
            forma_resultante="",
            accion="LINEA_ELIMINADA",
            contexto=contexto_raw
        ))
        return None

    return text


def main():
    files = iter_txt_files(ROOT_IN)
    if not files:
        raise FileNotFoundError(f"No se encontraron .txt en: {ROOT_IN}")

    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows: List[LogRow] = []

    for fp in files:
        id_archivo = fp.name
        ud_counter = 0
        linea_n = 0
        out_lines: List[str] = []

        with fp.open("r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.rstrip("\n")
                m = LABEL_RE.match(line)
                if not m:
                    continue

                linea_n += 1
                ud_counter += 1
                id_ud = f"UD{ud_counter:05d}"

                label = m.group("label")
                hablante = label
                rol = rol_from_label(label)

                # IMPORTANTE: NO limpiar prefijos (. TL / . 1. / etc.)
                contexto_raw = m.group("rest")

                norm_rest = apply_normas_sin_2_9_11(
                    contexto_raw=contexto_raw,
                    id_archivo=id_archivo,
                    id_ud=id_ud,
                    linea_n=linea_n,
                    hablante=hablante,
                    rol=rol,
                    rows=rows
                )

                if norm_rest is not None:
                    # Reconstruimos la línea completa conservando la etiqueta
                    out_lines.append(f"{label}: {norm_rest}")

        # salida TXT
        out_name = f"{fp.stem}_normas_1{fp.suffix}"
        out_path = out_dir / out_name
        out_path.write_text("\n".join(out_lines), encoding="utf-8")

    # salida CSV (UTF-8 con BOM + ; )
    with open(OUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([
            "id_archivo","id_ud","linea_n","hablante","rol",
            "norma_id","fenomeno","forma_original","forma_resultante",
            "accion","contexto"
        ])
        for r in rows:
            w.writerow([
                r.id_archivo, r.id_ud, r.linea_n, r.hablante, r.rol,
                r.norma_id, r.fenomeno, r.forma_original, r.forma_resultante,
                r.accion, r.contexto
            ])

    print("OK")
    print(f"- TXT normalizados en: {OUT_DIR}")
    print(f"- LOG CSV en:         {OUT_CSV}")
    print(f"- Archivos .txt:      {len(files)}")
    print(f"- Filas log:          {len(rows)}")


if __name__ == "__main__":
    main()

