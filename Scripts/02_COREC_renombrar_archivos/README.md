## Descripción

Renombrado masivo de archivos TXT del COREC conforme al nuevo sistema de identificación (IDs compuestos).
Este *script* aplica a un **lote** (lengua/enclave) y asume que los identificadores compuestos ya han sido generados y exportados a un CSV con una columna `id`.

## Entrada

Archivo CSV con columna `id` (por defecto: `/content/ids.csv` en Colab).
Archivos TXT de origen en una carpeta (por defecto: `/content/`), filtrados por un prefijo (`prefijo_archivos`, p. ej. `11_01`).

## Salida

Carpeta de salida con los TXT copiados y renombrados por ID (por defecto: `/content/Ren_Gijon`).
Archivo ZIP de la carpeta de salida (se descarga automáticamente en Colab).

## Configuración (parámetros editables)

En el script, edita la sección `CONFIG`:

- `csv_path`: ruta del CSV con IDs.
- `fila_inicio`, `fila_fin_excl`: rango de filas del CSV (inicio incluido, fin excluido).
- `carpeta_origen`: carpeta donde están los TXT originales.
- `prefijo_archivos`: prefijo para seleccionar el lote (ej. `11_01`).
- `carpeta_salida`: carpeta destino del renombrado.
- `LIMPIAR_TXT_EN_CONTENT`: si `True`, borra `/content/*.txt` antes de ejecutar (útil en Colab para evitar restos de ejecuciones previas).

### En Google Colab

1. Sube/coloca `ids.csv` en `/content/` (o ajusta `csv_path`).
2. Asegúrate de que los TXT del lote estén en `carpeta_origen`.
3. Ajusta `fila_inicio`, `fila_fin_excl`, `prefijo_archivos` y `carpeta_salida`.
4. Ejecuta el script.
5. Se generará un ZIP y se descargará automáticamente.

### En entorno local

1. Instala dependencias:
   - `pip install pandas`
2. Ajusta rutas (`csv_path`, `carpeta_origen`, `carpeta_salida`) a tu sistema.
3. Ejecuta:
   - `python 02_COREC_renombrar_archivos.py`
4. Se generará el ZIP en la ruta indicada (no hay descarga automática).

## Notas

- El script valida que el número de TXT encontrados coincide con el número de IDs seleccionados; si no coincide, detiene la ejecución.
- Se preserva el orden de las entrevistas ordenando por el sufijo numérico final del nombre de archivo.
