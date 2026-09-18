# FacelessYT

Operativa con datos para un canal de YouTube faceless en inglés, nicho *AI automation /
indie software business*.

La tesis está en [docs/00-estrategia.md](docs/00-estrategia.md). El resumen: el canal no es
el negocio, es el canal de distribución. AdSense es el suelo; la afiliación SaaS recurrente y
el producto propio son el negocio. Y hay una métrica que decide a los 90 días si se sigue o
se mata.

## Puesta en marcha

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e .
```

Después, la clave de la API (gratis, 10.000 unidades/día):

1. [console.cloud.google.com](https://console.cloud.google.com/) → nuevo proyecto
2. APIs y servicios → habilitar **YouTube Data API v3**
3. Credenciales → Crear credenciales → Clave de API
4. `cp .env.example .env` y pega la clave en `YOUTUBE_API_KEY`

## Comandos

### `check` — verificar la configuración

```bash
.venv/Scripts/python.exe -m facelessyt check
```

Comprueba la clave y resuelve los canales semilla del nicho. Los handles de YouTube cambian,
así que los que salgan en rojo hay que corregirlos en `niches/ai-automation.yaml`.
Coste: ~10 unidades de cuota.

### `mine` — encontrar temas con demanda probada

```bash
.venv/Scripts/python.exe -m facelessyt mine --niche ai-automation --min-score 3
```

Este es el núcleo. Para cada canal semilla calcula la **mediana de views de sus propios
vídeos** y busca los que la superan por 3x o más:

```
outlier_score = views del vídeo / mediana del canal
```

Normalizar contra el propio canal elimina el sesgo de tamaño: un vídeo con 40k views en un
canal que hace 400k de media es un fracaso; con 40k en un canal que hace 5k es una señal
enorme. Lo segundo es lo que buscamos, porque es prueba de que **el tema** tira, no el canal.

Regla operativa: **no se produce ningún vídeo con score < 3.**

Opciones útiles: `--days 90` (solo lo reciente), `--min-score 2` (nicho plano),
`--shorts` (incluir shorts), `--limit 60` (más filas).
Coste: ~3 unidades por canal semilla. Los resultados se guardan en `data/`.

### `track` — la métrica de corte

```bash
.venv/Scripts/python.exe -m facelessyt track
```

Necesita `MY_CHANNEL_ID` en `.env` (existe cuando exista el canal). Evalúa:

> **PASA si ≥3 vídeos superan 10.000 views Y la mediana del último tercio supera la del primero.**

Cada ejecución añade una línea a `data/history.jsonl`, para ver la evolución y no solo la
foto final. Ejecútalo una vez por semana.

### `packaging` — medir título y miniatura antes de producir

```bash
.venv/Scripts/python.exe -m facelessyt packaging --title "..." --thumb-text "..." --thumbnail miniatura.jpg
```

Mide la miniatura con las mismas métricas que `research` aplica a la competencia
(luminancia, saturación, píxeles negros) y comprueba que el texto nombra algo y el
título cabe en un móvil. `upload` ejecuta el mismo gate y **no sube** si falla.
Los umbrales y el porqué: [docs/09-diagnostico-2026-09-18.md](docs/09-diagnostico-2026-09-18.md).

### `video check` / `video render` — lint de gancho y ritmo, y montaje

```bash
.venv/Scripts/python.exe -m facelessyt.video check --script scripts/06-xxx.yaml
```

Rechaza guiones con la primera escena larga o sin payoff, con "this channel" /
"last video" en el gancho, con escenas de más de 55 palabras sobre una imagen, o de
más de 8 minutos. `render` (en Docker, ver abajo) añade zoom por escena, fundidos y
música de fondo (`--music` o `MUSIC_PATH`).

### `upload --publish-at` — subida programada

```bash
.venv/Scripts/python.exe -m facelessyt upload --video data/video/06.mp4 --title "..." --thumbnail t.jpg --thumb-text "..." --publish-at 2026-09-21T14:00
```

Sube privado y YouTube lo publica a esa hora. Un episodio entero, de guion a subida
programada: `tools/produce_episode.ps1`. Diagnóstico semanal: `tools/weekly_diagnose.ps1 -Register`.

## Docker

Para ejecutarlo sin instalar Python. Necesita `.env` con la clave:

```bash
docker compose run --rm facelessyt check
docker compose run --rm facelessyt mine --min-score 3
```

`data/` se monta como volumen, así que los resultados quedan en tu disco y no dentro
del contenedor. Tras cambiar código, añade `--build`.

Contenerizar esto no fue cosmético: destapó un bug real. `config.py` deducía la raíz
del proyecto subiendo dos directorios desde `__file__`, lo cual funciona con el repo
clonado y es falso cuando el paquete está instalado en `site-packages`. En local nunca
habría aparecido. Ahora hay `FACELESSYT_ROOT` y un test de regresión.

## Tests

```bash
.venv/Scripts/python.exe -m unittest discover -s tests
```

Cubren la lógica pura sin tocar la red: parseo de duraciones, cálculo de baseline, exclusión
de shorts y vídeos inmaduros, y los tres casos del veredicto (pasa, plano, hits sin tendencia).

## Estado

| Pieza | Estado |
|---|---|
| Selección de tema por outliers | **funciona** |
| Métrica de corte de 90 días | **funciona** (solo views) |
| CTR y retención (diagnóstico) | **funciona** (`diagnose`, OAuth) |
| Lint de gancho/ritmo y gate de packaging | **funciona** (`video check`, `packaging`) |
| Generación de guion | a mano, con [prompts](docs/prompts/hook-packaging.md) que pasan el lint |
| Voz (TTS) | **funciona** — Piper en el contenedor; ElevenLabs opcional |
| Render / montaje | **funciona** — ffmpeg en el contenedor, con movimiento y música |
| Subida programada | **funciona** (`upload --publish-at`, `tools/produce_episode.ps1`) |

Resultado a 28 días de los 5 primeros vídeos y lo que se cambió por ello:
[docs/09-diagnostico-2026-09-18.md](docs/09-diagnostico-2026-09-18.md).

## Estructura

```
docs/       estrategia, playbook, hallazgos y diagnósticos
tools/      producción de un episodio y diagnóstico semanal (PowerShell)
scripts/    guiones de los vídeos
niches/     definición de nichos (canales semilla, keywords, afiliados)
src/        el paquete
tests/      tests sin red
data/       salidas — ignorado por git
```
