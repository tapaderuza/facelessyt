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
.venv/Scripts/python.exe tests/test_core.py
```

Cubren la lógica pura sin tocar la red: parseo de duraciones, cálculo de baseline, exclusión
de shorts y vídeos inmaduros, y los tres casos del veredicto (pasa, plano, hits sin tendencia).

## Estado

| Pieza | Estado |
|---|---|
| Selección de tema por outliers | **funciona** |
| Métrica de corte de 90 días | **funciona** (solo views) |
| CTR y retención (diagnóstico) | pendiente — requiere YouTube Analytics API con OAuth |
| Generación de guion | pendiente |
| Voz (TTS) | pendiente |
| Render / montaje | pendiente — requiere ffmpeg (irá en el contenedor, no en tu máquina) |
| Subida automática | pendiente — requiere OAuth |

Lo pendiente es deliberado: no tiene sentido automatizar la producción antes de saber si el
nicho responde. Primero `mine`, primeros vídeos a mano, y solo entonces se automatiza lo que
duela.

## Estructura

```
docs/       estrategia, playbook y hallazgos de cada minado
scripts/    guiones de los vídeos
niches/     definición de nichos (canales semilla, keywords, afiliados)
src/        el paquete
tests/      tests sin red
data/       salidas — ignorado por git
```
