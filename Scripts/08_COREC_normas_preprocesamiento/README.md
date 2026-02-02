##  08_COREC_normas_preprocesamiento_I

## Descripción
Este script aplica la fase **Normalización I** a entrevistas ya **segmentadas discursivamente**. Mantiene las etiquetas de turno (`I1:`, `E1:`, `INF:`, `ENT:`…) y procesa el contenido posterior a la etiqueta.

Genera:
- **TXT normalizados** (`Salida_TXT_normas_1`)
- **Log CSV de trazabilidad** (`Log_normas_1.csv`)

**Orden de ejecución normativa:** `7 → 5 → 1 → 4 → 6 → 3 → 8 → 10`

## Entrada
- **Carpeta:** `Preprocesamiento_linguistico/1_Textos_segmentacion_discursiva/`
- **Archivos:** `<ID_compuesto>_seg.txt`
- **Codificación:** `UTF-8`

## Salida
- **TXT:** `Preprocesamiento_linguistico/2_Salida_TXT_normas/Salida_TXT_normas_1/`  
  - `<ID_compuesto>_seg_normas_1.txt`
- **Log:** `Preprocesamiento_linguistico/3_Logs/Log_normas_1/Log_normas_1.csv`  
  - **Separador:** `;`  
  - **Codificación:** `UTF-8-SIG`

## Requisitos
- **Python:** 3.10+
- **Hunspell**

## Colab
```bash
apt-get install -y hunspell hunspell-es libhunspell-dev
pip install hunspell
```
## Local 
Instalar hunspell + diccionarios es_ES del sistema + wrapper hunspell para Python.

## Registro (Log_normas_1.csv)

Cada evento registrado incluye:
id_archivo, id_ud, linea_n, hablante, rol, norma_id, fenomeno, forma_original, forma_resultante, accion, contexto


## Uso
Desde la raíz del repositorio
```
python 08_COREC_normas_preprocesamiento_I.py
```
## Colab (opcional)

from google.colab import drive
drive.mount("/content/drive")


Ajusta REPO_ROOT en CONFIG

Ejecuta:

```
!python 08_COREC_normas_preprocesamiento_I.py
```



