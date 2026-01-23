## Descripción
Este *script* segmenta automáticamente las transcripciones ortográficas del COREC. Para ello, toma como fronteras candidatas las marcas de pausa `/` y `//` (normalizadas a `/`).
La decisión de corte combina rasgos morfosintácticos (spaCy) y pragmático-discursivos, con un mecanismo de **bloqueo estructural** para preservar dependencias proyectadas.

## Entrada
- Local: `Corpus/TXT/Ren_limpio_fase_0/`
- Colab: `.../Corpus/TXT/Ren_limpio_fase_0/` (bajo `REPO_ROOT`)

## Salida
- Local: `Preprocesamiento_lingüistico/1_Textos_segmentacion_discursiva/`
- Colab: `Preprocesamiento_lingüistico/1_Textos_segmentacion_discursiva_test/`

**Archivos generados**
- Por cada `.txt` de entrada: un archivo con sufijo `_seg.txt` (conserva el subárbol relativo a `ROOT_IN`)

## Parámetros editables
- `MIN_WORDS_FOR_SLASH_CUT`: umbral mínimo (`8`)
- `NEXOS`: conectores/nexos bloqueantes en posición final
- `PATRONES_CIERRE`: cierres pragmáticos lexicalizados
- `PREVIEW_N`: nº de líneas mostradas por archivo en la vista previa (por defecto `5`)

## Requisitos
- Python 3.10+
- spaCy
- Modelo spaCy español: `es_core_news_lg`

## Uso

## En local (desde la raíz del repositorio)
Instala spaCy y el modelo:
```bash
python -m pip install -U spacy
python -m spacy download es_core_news_lg
```
Ejecuta:
```bash
python 07_COREC_segmentacion_discursiva.py
```
## En Colab

Instala spaCy y descarga el modelo:

```bash
!pip -q install -U spacy
!python -m spacy download es_core_news_lg -q
```

Si usas rutas bajo /content/drive/..., monta Drive:

descomenta en el script:
```python
drive.mount("/content/drive")
```
Ejecuta:

```bash
!python 07_COREC_segmentacion_discursiva.py
```

