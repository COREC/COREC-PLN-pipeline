## Descripción

Este script selecciona automáticamente una **muestra prototípica** del corpus COREC por **lengua de contacto**, a partir del CSV generado en el análisis de frecuencias. La selección se basa en **distancia Manhattan a la mediana** sobre ratios lingüísticos y una penalización por ruido.

## Entrada
Archivo CSV (frecuencias):
`Frecuencias_basicas/analisis_de_frecuencias_def.csv`  
En Colab, `Frecuencias_basicas/analisis_de_frecuencias_def_test.csv`  
Separador: `;`  
Codificación: UTF-8

## Salida
Carpeta de salida:
- `Muestras_prototipicas/muestras_por_lengua/`  
En Colab, por defecto:
- `Muestras_prototipicas/muestras_por_lengua_test/`

Archivos generados:
- `seleccion_<lengua>.csv` (uno por lengua)
- `muestra_prototipica_global.csv` (todas las lenguas concatenadas)

## Criterio de selección
Para cada lengua de contacto, se calculan las siguientes métricas:

- `ratio_entrevistado` = `prop_entrevistado`
- `ratio_types` = `types_total / tokens_totales`
- `ratio_freq_2_5` = `freq_2_5 / types_total`
- `ratio_ruido` = `marcas_ruido / tokens_totales` (penalización)

Se calcula la **distancia total** como suma de distancias absolutas a la **mediana** de cada métrica:

- `dist_total = |x - mediana(x)|` (sumada en las métricas principales)  
y se añade la penalización por ruido:
- `dist_total += ratio_ruido`

Se seleccionan los **K** documentos con menor `dist_total`.

## Campos añadidos en la salida
- `dist_total`: distancia total (con penalización por ruido)
- `k_orden`: orden 1..K dentro de la selección de cada lengua

## Configuración (parámetros editables)
En el script:
- `CSV_BASE`: ruta del CSV de entrada
- `OUT_DIR`: carpeta de salida
- `K`: nº de entrevistas seleccionadas por lengua (por defecto 5)

## Uso
Desde la raíz del repositorio:

```bash
python 06_COREC_seleccion_muestra_prototipica.py
```
En Colab:

Descomenta `drive.mount("/content/drive")` en el script y ejecuta:

```bash
!python 06_COREC_seleccion_muestra_prototipica.py
```

