# -*- coding: utf-8 -*-
"""
01_COREC_PDF_a_TXT

Conversión de PDFs (contenidos en un ZIP) a TXT.

- En Google Colab: monta Google Drive automáticamente.
- En entorno local: omite el montaje y usa rutas locales en zip_path/extract_path/txt_output.
"""

# === (Opcional) Montaje de Google Drive si estás en Colab ===
try:
    from google.colab import drive  # type: ignore
    drive.mount("/content/drive")
except Exception:
    print("No estás en Google Colab: omitiendo drive.mount().")

# === CONFIG (edita estas rutas según tu entorno) ===
zip_path = "/content/drive/MyDrive/COREC/PDFs/<paquete_pdf_originales>.zip"
extract_path = "/content/drive/MyDrive/COREC/PDFs/extraidos"
txt_output = "/content/drive/MyDrive/COREC/TXT"

import os
import zipfile
import fitz  # PyMuPDF

os.makedirs(extract_path, exist_ok=True)
os.makedirs(txt_output, exist_ok=True)

# 1) Extraer ZIP
with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(extract_path)

print("PDFs extraídos en:", extract_path)

# 2) Convertir cada PDF a TXT
for archivo in os.listdir(extract_path):
    if archivo.lower().endswith(".pdf"):
        ruta_pdf = os.path.join(extract_path, archivo)
        base = os.path.splitext(archivo)[0]
        ruta_txt = os.path.join(txt_output, base + ".txt")

        print(f"Convirtiendo: {archivo} -> {base}.txt")

        texto_total = []
        with fitz.open(ruta_pdf) as doc:
            for pagina in doc:
                texto_total.append(pagina.get_text())

        with open(ruta_txt, "w", encoding="utf-8") as f:
            f.write("\n".join(texto_total))

print("CONVERSION COMPLETA")
