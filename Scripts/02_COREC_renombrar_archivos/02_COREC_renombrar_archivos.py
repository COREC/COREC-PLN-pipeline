import pandas as pd
from pathlib import Path
import shutil
import glob
import os

# --- Colab opcional ---
try:
    from google.colab import files  # type: ignore
    EN_COLAB = True
except Exception:
    EN_COLAB = False

# =========================
# CONFIG (EDITAR AQUÍ)
# =========================
csv_path = "/content/ids.csv"              # en local: pon ruta local, p.ej. "ids.csv"
fila_inicio = 0                           # inclusive
fila_fin_excl = 4                         # exclusiva

carpeta_origen = Path("/content/")         # en local: Path(".") o la ruta a tus TXT
prefijo_archivos = "11_01"                # ej. "11_01"

carpeta_salida = Path("/content/Ren_Gijon")# cambia el nombre por el enclave/lote

# Limpieza opcional (como en tu versión original)
LIMPIAR_TXT_EN_CONTENT = False            # True si quieres borrar /content/*.txt antes de empezar
# =========================

if LIMPIAR_TXT_EN_CONTENT:
    for f in glob.glob("/content/*.txt"):
        os.remove(f)

df = pd.read_csv(csv_path)
ids = df["id"].iloc[fila_inicio:fila_fin_excl].tolist()

print("IDs seleccionados:")
for i, x in enumerate(ids, start=1):
    print(i, x)

carpeta_salida.mkdir(exist_ok=True)

archivos = sorted(
    (
        f for f in carpeta_origen.iterdir()
        if f.is_file() and f.suffix.lower() == ".txt" and f.name.startswith(prefijo_archivos)
    ),
    key=lambda x: int(x.stem.split("_")[-1])
)

print(f"\nArchivos encontrados: {len(archivos)}")
print(f"IDs seleccionados:    {len(ids)}")

if len(archivos) != len(ids):
    raise ValueError("No coincide el número de archivos y de IDs. Revisa el rango o el prefijo.")

for archivo, nuevo_id in zip(archivos, ids):
    nuevo_nombre = carpeta_salida / f"{nuevo_id}.txt"
    shutil.copy2(archivo, nuevo_nombre)
    print(f"{archivo.name}  ->  {nuevo_nombre.name}")

print(f"\nListo: archivos copiados y renombrados en '{carpeta_salida.name}'.")

zip_base = str(carpeta_salida)
zip_path = zip_base + ".zip"
shutil.make_archive(zip_base, "zip", carpeta_salida)

if EN_COLAB:
    files.download(zip_path)
else:
    print("ZIP creado:", zip_path)

