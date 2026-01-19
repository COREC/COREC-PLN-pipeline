# FASE 1 — Análisis de frecuencias lingüísticas básicas (COREC)

## Descripción

Esta fase tiene como objetivo **caracterizar cuantitativamente cada entrevista del corpus COREC** mediante un conjunto de atributos lingüísticos, con una doble finalidad: por un lado, servir de base para la **selección de una muestra prototípica** del corpus y, por otro, facilitar el **estudio cuantitativo global** del mismo.
El análisis se realiza **exclusivamente en memoria**, sin modificar los archivos originales, y respeta los rasgos propios de la oralidad y las anotaciones metalingüísticas del corpus.

## Entrada

- Carpeta de entrada:  
  `COREC/Corpus/TXT/Ren_limpio_fase_0/`
- Archivos TXT preprocesados en la FASE 0, con una entrevista por archivo y turnos de habla estandarizados.

## Salida

- Archivo CSV:  
  `COREC/Frecuencias_basicas/analisis_de_frecuencias_def.csv`
- Codificación: UTF-8  
- Separador: `;`

En entorno Colab, el archivo de salida se genera con sufijo `_test` para evitar sobrescrituras accidentales.

## Atributos calculados

El script calcula, para cada entrevista, los siguientes atributos:

- **tokens_totales**: número total de tokens lingüísticos.
- **tokens_entrevistado**: número de tokens producidos por el informante.
- **tokens_entrevistador**: número de tokens producidos por el entrevistador.
- **porc_entrevistado**: proporción de habla atribuible al informante.
- **types_total**: número de formas léxicas distintas.
- **hapax**: número de palabras con frecuencia 1.
- **freq_2_5**: número de palabras con frecuencia entre 2 y 5.
- **%_freq_2_5**: porcentaje de palabras con frecuencia entre 2 y 5.
- **marcas_ruido**: número de marcas de contenido no inteligible.
- **marcas_aclaracion**: número de aclaraciones editoriales del transcriptor.

## Reglas de análisis aplicadas

Las reglas se aplican **en memoria**, con el fin de preservar los textos originales:

### Identificación de hablantes
- Se detectan las etiquetas de turno situadas al inicio de cada línea.
- Las etiquetas no se contabilizan como tokens.
- Los tokens se asignan al informante o al entrevistador según la etiqueta detectada, garantizando la trazabilidad del origen de la producción lingüística.

### Tratamiento del contenido anotado
- El texto se segmenta para distinguir entre producción lingüística y anotaciones editoriales.
- Se excluyen del cómputo los contenidos entre `[ ]`, `( )` y `< >`.
- Las anotaciones que comienzan por `IN` (Ininteligible) se contabilizan como **ruido**.
- El resto de anotaciones se contabilizan como **marcas de aclaración**.
- Ninguna anotación editorial se incorpora al conteo léxico.

### Normalización y filtrado de tokens
Para el resto de las formas léxicas:

- Se eliminan los dos puntos que indican marcas fonéticas.
- No se contabilizan marcas prosódicas (`/`, `//`, `///`).
- Se descartan etiquetas de turno que no están en posición inicial de línea.
- Se elimina la puntuación lateral.
- Se limpian guiones internos (`bue-no → bueno`).
- Se filtran únicamente tokens alfabéticos (acentos incluidos).
- Se descartan las marcas `tl`, `sbx` y `r`.
- Se normaliza a minúsculas **solo para el cómputo**.

Cada token válido se asigna finalmente al informante o al entrevistador.

## Campos del archivo de salida

El archivo CSV generado contiene los siguientes campos, en este orden:

- `id_muestra`
- `lengua_contacto`
- `pais_region`
- `tokens_totales`
- `tokens_entrevistado`
- `tokens_entrevistador`
- `porc_entrevistado`
- `types_total`
- `hapax`
- `freq_2_5`
- `%_freq_2_5`
- `marcas_ruido`
- `marcas_aclaracion`

Nota: los campos id_muestra, lengua_contacto y pais_region se escriben con un apóstrofo inicial (') para que Excel no altere los identificadores. Si no se usa Excel, ese apóstrofo puede ignorarse.
## Uso

Desde la raíz del repositorio:

```bash
python 05_COREC_analisis_frecuencias.py
