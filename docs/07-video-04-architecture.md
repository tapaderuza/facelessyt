# Episodio 04 — arquitectura correctora

Decisión y producción: [paquete del Episodio 04](../production/04-local-memory/README.md).

## Qué cambia

`youtube.Video` y `miner.Outlier` añaden `channel_id` y/o `thumbnail_url` como campos
opcionales, manteniendo los constructores y snapshots anteriores. La Data API se
consulta ya por snippet; se conserva la miniatura de mayor área disponible.

`mine(..., coverage=dict)` permite guardar todos los vídeos de la ventana que se
recuperaron de las semillas, incluidos los no-outliers y canales sin baseline. `mine`
del CLI activa esta captura y `save` la incluye. La firma de retorno sigue siendo
`(outliers, warnings)`. Ni esa cobertura ni el conteo de canales son un censo de YouTube.

`opportunities.py` agrupa por canal, evita multiplicar evidencia por varios uploads
del mismo creador y separa tamaños desconocidos. Conserva conteos por tamaño tanto
en outliers como en cobertura cuando existe. Para el snapshot antiguo declara
`scope=outliers_only` y `market_saturation=null`. Usa ID si está disponible y marca
el fallback a nombre; colisiones/renombrados pueden requerir revisión manual.
Cuando el snapshot incluye el registro de canales muestreados, añade la proporción
de canales que cubren el tema dentro de cada banda de tamaño. El denominador sigue
siendo la muestra, no el mercado; bandas sin observaciones quedan null.

La mediana del tema se calcula como mediana de medianas por canal. La selección del
Episodio 04 está declarada en `TOPICS` y en el informe, no disimulada como un modelo
estadístico de éxito. El catálogo de publicados se basa en la confirmación del usuario.
La semántica no se resuelve solo por igualdad de títulos: se excluyen además áreas
adyacentes a los episodios previos y se exige revisión editorial.

`visual_research.py` descarga por ID solo desde HTTPS en `i.ytimg.com`, no sigue
redirecciones, limita bytes/píxeles y rechaza placeholders pequeños. Para snapshots
antiguos sin URL intenta maxres y después hq. Caché por vídeo con SHA-256 y fecha de
captura; `--refresh` actualiza explícitamente. No hay secretos ni OAuth en este paso.

OpenCV obtiene desviación estándar de gris y amplitud p95–p05 normalizadas, más
saturación media en HSV. Tesseract devuelve palabras, confianza y bounding boxes.
Se conserva tanto conteo total como prominente (altura >=6%, heurístico). OCR fallido
es null/partial; cero significa ejecución correcta sin tokens aceptados. Cada error
de descarga queda en el informe; el CLI devuelve 1 ante resultados incompletos.

Dependencias visuales opcionales: `.[vision]`; Tesseract es una dependencia del sistema.
`Dockerfile.research` evita instalarla en Windows. El minero normal sigue funcionando
sin OpenCV/Tesseract. No se han modificado OAuth, tokens, publicación ni renderizadores
anteriores. No se añadió código a la carpeta ignorada `scripts/` para este episodio.

## Uso integrado

```text
mine --thumbnails   -> nuevo snapshot con cobertura -> miniaturas de cada outlier
research            -> último snapshot por generated_at -> catálogo/criterios
                    -> candidato -> miniaturas automáticas -> informe + revisión
research --all-thumbnails -> extiende el análisis a todos los outliers del snapshot
research --skip-visuals   -> ranking local sin red ni dependencias visuales
```

El análisis de imágenes es automático dentro de `research` por defecto. En `mine`
se activa con `--thumbnails` porque las dependencias visuales son opcionales. El
comando no estima CTR. Las métricas propias deben obtenerse con autorización o
exportaciones del propietario; no se deducen de views/likes/saturación de color.

## Evidencia y verificación

- Snapshot usado: `data/outliers-ai-automation-2026-09-10.json`, sin alterar.
- Informe calculado: `data/research/04-local-memory/opportunities.json`.
- 26 capturas y mediciones: `data/research/04-local-memory/thumbnails/report.json`.
- Revisión humana de las dos referencias del tema y del outlier global: `visual-review.md`.
- Pruebas: `tests/test_research.py`, `tests/test_visual_research.py`; más tests previos.
- `memory_budget.py`: demostración determinista separada del minero, sin carga de LLM.
- `build_package.py`: continuidad de escenas, referencias a evidencia, beats <=6 s,
  duración/fotogramas y velocidad de locución plausible. No sustituye QA audiovisual.
- `test_animatic.cjs`: estado SVG determinista y cambios geométricos, no test de navegador.

## Límites deliberados

No prueba causal de faceless, estimador de vistas, clon de miniaturas, scraping de
Analytics privados, instalación de modelos, benchmark inventado ni publicación.
Para estimar competencia fuera de las semillas haría falta ampliar de forma explícita
el diseño de muestreo. Para medir efecto de empaquetado necesitamos datos propios.
La ausencia de grandes en dos outliers locales es una observación de esa muestra,
no una promesa de que no compitan en ese mercado.

Las afirmaciones causales del hallazgo original (“prueba de que tira el tema y no
el canal”) quedan corregidas por este documento y por la docstring del minero. El
documento histórico se preserva para trazabilidad.
