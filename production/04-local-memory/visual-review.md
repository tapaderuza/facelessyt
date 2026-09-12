# Ingeniería inversa visual — revisión del Episodio 04

Capturas actuales descargadas el 12 de septiembre de 2026. No sabemos si eran
las miniaturas expuestas durante la acumulación de las views del snapshot del día 10.
No se conoce el CTR de estos vídeos. Ni la saturación ni el contraste lo estiman.

## Referencias del tema elegido

| Referencia | Contraste σ(gris)/255 | Saturación media HSV/255 | OCR automático | Revisión manual del titular |
|---|---:|---:|---:|---|
| IndyDevDan, `00Y-p62sk0s` | 0,3172 | 0,1643 | 2 | 3 elementos: M5 / GEMMA4 / MLX. OCR omite M5. |
| AICodeKing, `CpMCYO2oWBI` | 0,2953 | 0,3324 | 48 | 4 elementos: 5.3 / FLASH / LOCAL / OPUS. Además, badge Local Mode y texto pequeño de interfaz. |

Las medidas se calculan sobre la imagen RGB completa, sin recorte, incluyendo
cualquier borde o interfaz. OCR: Tesseract, inglés, PSM 11, confianza >=50.
El informe conserva texto, confianza y cajas. El conteo de palabras prominentes
usa altura >=6% de la imagen: es otro filtro heurístico, no verdad de referencia.
Los tokens de números/productos también cuentan; no es un análisis lingüístico.

El original de IndyDevDan presenta un portátil y manos sobre una superficie oscura,
titular superior muy grande y un acento amarillo. No presenta un rostro.
El de AICodeKing presenta dos bandas grandes de texto, blanco/negro y azul/blanco,
una interfaz al fondo y un indicador de modo local a la derecha. No presenta un rostro.
Esto describe las imágenes: no confirma que sus vídeos completos sean faceless ni
separa el efecto de la autoridad de sus creadores.

## Traducción al diseño propio

Decisión: titular corto y grande + un único objeto técnico comprensible.
La baja saturación de IndyDevDan evita justificar una paleta multicolor como
condición para funcionar. La separación claro/oscuro importa para leer nuestra
propuesta; las cifras observadas no son un objetivo óptimo demostrado.

Miniatura A: **IT FITS?** a la derecha. A la izquierda, contenedor de memoria con
pesos verdes y conversación azul que rebasa el techo en rojo. Nada de logos de
modelos, rostros, portátil de una marca o una interfaz que no hayamos ejecutado.
El desbordamiento plantea el conflicto; el título lo explica como conversación.

Miniatura B: misma composición, **TOO MUCH CONTEXT**. Mantener el resto constante
permite interpretar mejor una futura comparación propia. No prometemos un uplift.
Revisar a 320×180 que se distingan contenedor, desbordamiento y pregunta sin leer
etiquetas pequeñas. La animación del segundo cero debe pagar esta misma promesa.

El mayor outlier global, `9d5bzxVsocw`, también se inspeccionó: fondo negro,
titular claro, iconos y flechas. OCR devuelve un falso positivo adicional a
“Harness 2.0”. Es una referencia secundaria de jerarquía, no razón para repetir
el tema de harnesses ya cubierto en el Episodio 03.

## Trazabilidad

- Originales y hashes: `data/research/04-local-memory/thumbnails/*.capture.json`.
- Informe completo de las 26 imágenes: `data/research/04-local-memory/thumbnails/report.json`.
- No reutilizar las imágenes descargadas como arte de nuestra miniatura ni incluirlas
  sin revisión de derechos en el vídeo final. Se descargaron para análisis interno.
- No convertir OCR=0 en «miniatura sin texto» sin inspección; OCR no disponible es null.

Referencias técnicas: [OpenCV, conversiones de color](https://docs.opencv.org/4.13.0/d8/d01/group__imgproc__color__conversions.html),
[Tesseract, TSV y modos de segmentación](https://tesseract-ocr.github.io/tessdoc/Command-Line-Usage.html),
[YouTube, metadatos públicos de miniaturas](https://developers.google.com/youtube/v3/docs/thumbnails),
[YouTube Analytics, autorización del propietario del canal](https://developers.google.com/youtube/analytics/channel_reports).
