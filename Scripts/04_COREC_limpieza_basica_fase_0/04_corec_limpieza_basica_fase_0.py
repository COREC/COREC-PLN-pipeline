# -*- coding: utf-8 -*-
import os, re
"""
1) Edita CONFIG si ejecutas en local
"""

# --- Colab opcional ---
try:
    from google.colab import drive  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False


# CONFIG (EDITAR AQUÍ)
# =========================
# --- LOCAL (por defecto; ejecutando desde la raíz del repo COREC) ---
ROOT_IN  = "Corpus/TXT/Ren"
ROOT_OUT = "Corpus/TXT/Ren_limpio_fase_0"

# --- COLAB (opcional; carpeta COREC subida a MyDrive) ---
if EN_COLAB:
    REPO_ROOT = "/content/drive/MyDrive/COREC"
    ROOT_IN  = f"{REPO_ROOT}/Corpus/TXT/Ren"
    ROOT_OUT = f"{REPO_ROOT}/Corpus/TXT/Ren_limpio_fase_0_test"
# =========================

# --- Si quieres montar Drive en Colab, descomenta ---
# if EN_COLAB:
#     drive.mount("/content/drive")


# --------- PATRONES -------

# Etiquetas de turno: E, I, INF, ENT, con o sin número, y combinadas con "/"
TAG_LABEL = r'(?:INF|ENT|E|I)(?:\d+)?'
TAG_SEQ   = rf'(?:{TAG_LABEL}(?:/{TAG_LABEL})*)'

# Línea de turno (permite ":", "=", o solo espacio tras la etiqueta)
TAG_TURN = re.compile(
    rf'^\s*({TAG_SEQ})\s*(?:[:=]\s*|\s+)?(.*)$'
)

# Línea con solo la etiqueta (para unir con la siguiente)
TAG_ONLY = re.compile(
    rf'^\s*({TAG_SEQ})\s*(?:[:=]\s*)?$'
)

# Turno con contenido
TURN_WITH_CONTENT = re.compile(
    rf'^\s*({TAG_SEQ})\s*(?:[:=]\s*|\s+)\S'
)

ONLY_DIGITS  = re.compile(r'^\s*\d+\s*$')
REMOVE_COREC = re.compile(r'corec', re.IGNORECASE)

# --------- NO TOCAR CORCHETES / ANGULARES / LLAVES / PARÉNTESIS ---------
def clean_outside_brackets(text):
    # protegemos [ ], < >, { }, ( )
    parts = re.split(r'(\[[^\]]*\]|<[^>]*>|\{[^}]*\}|\([^)]*\))', text)
    out = []
    for i, p in enumerate(parts):
        if i % 2 == 1:  # dentro de marca protegida
            out.append(p)
        else:
            # espacios múltiples -> 1
            p = re.sub(r'[ \t]+', ' ', p)
            # espacio tras puntuación fuerte si falta
            p = re.sub(r'(\.{3}|[.!?:;])(?=\S)', r'\1 ', p)

            # ----  espacio ANTES de / y // si están pegados a palabra ----
            p = re.sub(r'([^\s/])//', r'\1 //', p)       # ...palabra// -> palabra //
            p = re.sub(r'([^\s/])/(?!/)', r'\1 /', p)    # ...palabra/  -> palabra /

            # ---- espacio DESPUÉS de / y // ----
            p = re.sub(r'//\s*([^\s])', r'// \1', p)     # //palabra -> // palabra
            p = re.sub(r'/\s*([^\s/])', r'/ \1', p)      # /palabra  -> / palabra

            out.append(p)
    return ''.join(out)

# --------- LIMPIEZA DE UNA LÍNEA ---------
def clean_line(line):
    line = line.rstrip('\n')
    m = TAG_TURN.match(line)
    if m:
        tag = m.group(1)            # E, E1, INF, ENT2, E1/E2, etc.
        rest = m.group(2).strip()   # contenido tras ":", "=", o espacio
        if not rest:
            return f"{tag}:\n"
        rest = clean_outside_brackets(rest)
        # normalizamos SIEMPRE a "ETIQUETA: contenido"
        return f"{tag}: {rest}\n"
    else:
        body = clean_outside_brackets(line.strip())
        return body + ("\n" if body else "")

# --------- PROCESAR UN TXT ---------
def process_file(path_in, path_out):
    with open(path_in, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    # 1. quitar líneas solo números y líneas con "COREC" que no sean turnos
    filtered = []
    for ln in lines:
        if ONLY_DIGITS.match(ln):
            continue
        if REMOVE_COREC.search(ln) and not TAG_TURN.match(ln):
            continue
        filtered.append(ln)
    lines = filtered

    # 2. Unir etiqueta sola + línea siguiente
    merged = []
    i = 0
    while i < len(lines):
        ln = lines[i]
        if TAG_ONLY.match(ln) and i+1 < len(lines) and not TAG_TURN.match(lines[i+1]):
            tag = TAG_ONLY.match(ln).group(1)
            merged.append(f"{tag}: {lines[i+1].lstrip()}")
            i += 2
            continue
        merged.append(ln)
        i += 1

    # 3. Limpieza y quitar vacías internas
    cleaned = []
    for ln in merged:
        out = clean_line(ln)
        if out.strip():
            cleaned.append(out)

    # 4. Unir TODAS las líneas de una misma intervención
    #    (desde un turno hasta el siguiente turno)
    joined = []
    for ln in cleaned:
        text = ln.rstrip()
        if TAG_TURN.match(text):        # nueva intervención
            joined.append(text)
        else:                           # continuación del turno anterior
            if joined:
                joined[-1] = joined[-1].rstrip() + " " + text
            else:
                joined.append(text)

    # 5. Insertar 1 línea vacía entre intervenciones
    final = []
    for idx, text in enumerate(joined):
        if idx > 0:
            final.append("\n")
        final.append(text + "\n")

    # Guardar
    os.makedirs(os.path.dirname(path_out), exist_ok=True)
    with open(path_out, "w", encoding="utf-8") as f:
        f.writelines(final)

# --------- RECORRER TODAS LAS SUBCARPETAS ---------
total_txt = 0

for dp, _, files in os.walk(ROOT_IN):
    rel = os.path.relpath(dp, ROOT_IN)
    out_dir = os.path.join(ROOT_OUT, rel) if rel != "." else ROOT_OUT
    for name in files:
        if name.lower().endswith(".txt"):
            src = os.path.join(dp, name)
            dst = os.path.join(out_dir, name)
            print("→ limpiando:", src)
            process_file(src, dst)
            total_txt += 1

print(f"Limpieza finalizada (FASE 0). Archivos procesados: {total_txt}")


