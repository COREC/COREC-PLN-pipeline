## Objetivo
Estandarizar la estructura de los textos sin introducir normalización lingüística profunda. Se preservan los rasgos propios de la oralidad y las anotaciones metalingüísticas del corpus.

## Entrada
- Carpeta: `Corpus/TXT/Ren/`
- Archivos TXT renombrados con identificadores compuestos.

## Salida
- Carpeta paralela: `Corpus/TXT/Ren_limpio_fase_0/`
- Estructura de subcarpetas idéntica a la de entrada.

## Operaciones realizadas
- Estandarización de los turnos de habla (`E`, `I`, `INF`, `ENT`).
- Fusión de líneas cuando la etiqueta de turno aparece aislada.
- Eliminación de líneas formadas únicamente por números o referencias residuales.
- Preservación estricta del contenido entre corchetes `[ ]`, angulares `< >`, llaves `{ }` y paréntesis `( )`.
- Normalización de espacios y barras prosódicas (`/`, `//`).
- Unificación de las líneas correspondientes a una misma intervención.

## Uso
Ejecutar desde la raíz del repositorio:

`python 04_corec_limpieza_basica_fase_0.py`

**Nota (Colab):** por defecto la salida se dirige a `Corpus/TXT/Ren_limpio_fase_0_test/` para evitar la sobrescritura de datos.
