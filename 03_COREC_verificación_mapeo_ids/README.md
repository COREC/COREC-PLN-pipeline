# Verificación de correspondencia entre IDs y archivos

Este script realiza una validación de control entre los identificadores del
archivo `ids.csv` y los archivos de texto del corpus COREC, así como de la
coherencia estructural y de contenido entre las carpetas `Original` y `Ren`.

## Qué comprueba

- Correspondencia 1:1 entre IDs del CSV y archivos `.txt`
- Detección de archivos sobrantes o faltantes
- Coherencia de ubicación por carpeta
- Coincidencia de contenido (primera línea) entre versiones `Original` y `Ren`

## Ejecución en local

Desde la raíz del repositorio:

python Scripts/03_COREC_verificación_mapeo_ids/03_COREC_verificación_mapeo_ids.py

## Ejecución en Google Colab

En una celda de Colab:

from google.colab import drive
drive.mount("/content/drive")

A continuación, ejecuta el script:

!python /content/drive/MyDrive/COREC/Scripts/03_COREC_verificación_mapeo_ids/03_COREC_verificación_mapeo_ids.py
