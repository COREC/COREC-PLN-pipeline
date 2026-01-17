# 01_COREC_PDF_a_TXT

Scripts para la conversión de las transcripciones ortográficas del Corpus Oral de Referencia del Español en Contacto (COREC) desde archivos PDF a TXT.

## Entrada

Paquetes ZIP que contienen los PDFs originales de las transcripciones ortográficas del COREC.

## Salida

Archivos planos TXT para su posterior preprocesamiento lingüístico.

## Dependencias

- PyMuPDF (`fitz`) — requerido
- `zipfile` (biblioteca estándar de Python)
- Google Colab (`google.colab.drive`) — solo si se ejecuta en Colab

## Entorno recomendado

Google Colab o entorno local con Python 3.x

### En Google Colab

1. Monta Google Drive.
2. Edita `zip_path`, `extract_path` y `txt_output`.
3. Ejecuta el script.

### En entorno local

1. Instala dependencias:
   - `pip install pymupdf`
2. Edita `zip_path`, `extract_path` y `txt_output` con rutas locales.
3. Ejecuta:
   - `python 01_COREC_PDF_a_TXT.py`

## Notas

- Las rutas de entrada y salida son configurables y deben adaptarse al entorno de trabajo.


