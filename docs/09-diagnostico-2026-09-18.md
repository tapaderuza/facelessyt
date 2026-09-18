# Diagnóstico a 28 días (2026-09-18) y qué cambia en el pipeline

Cinco vídeos publicados entre el 10 y el 13 de septiembre. Datos de YouTube Studio,
ventana 21 ago – 17 sep:

| | Valor | Umbral de docs/00-estrategia | Veredicto |
|---|---|---|---|
| Impresiones de miniatura | 4.200 | — | YouTube **sí** los enseña (42% browse, 34% sugeridos) |
| CTR | **1,0%** (ep. 5: 0,4%) | > 4% | **packaging roto** |
| Duración media vista | 0:55 | — | se van en el primer minuto |
| Retención media | 5,6% (ep. 1) … 22,6% (ep. 5) | > 40% | **gancho y ritmo rotos** |
| Espectadores nuevos | 96,6% | — | nadie vuelve (1 suscriptor) |

Con la tabla de diagnóstico de la estrategia: las tres métricas fallan, así que
**todavía no se puede decir nada del nicho**. Primero se arregla lo arreglable.

## Por vídeo

| Ep. | Título | Dur. | Views | AVD | Retención |
|---|---|---|---|---|---|
| 1 | I Built an AI Agent That Picks My YouTube Videos For Me | 20:10 | 101 | 1:07 | 5,6% |
| 2 | My YouTube Tool Said This Topic Was Hot. It Was a Trap. | 16:14 | 21 | 0:25 | 2,6% |
| 3 | I Built an AI Agent That Has to Prove It's Right | 11:21 | 23 | 1:21 | 12,0% |
| 4 | Your AI Model Fits. Your Conversation Doesn't. | 6:00 | 8 | 0:11 | 3,1% |
| 5 | I Doubled the Workers. The Bottleneck Didn't Move. | 3:51 | 27 | 0:52 | 22,6% |

El único con movimiento continuo en pantalla (ep. 5, simulación canvas) retuvo 4x
más que los de planos fijos. Es la señal más clara de todo el conjunto.

## Causas, en el código

Lo primero que hay que decir: **no hay ningún LLM en el pipeline**. Los guiones son
YAML escritos a mano, los visuales son PNG dibujados con Pillow (`scenes.py`) o
canvas (ep. 5), la voz es Piper `en_US-lessac-medium`, y la miniatura se hizo fuera.
No había prompts que mejorar; había reglas que no existían.

### 1. Miniaturas: oscuras, sin color y sin referente (CTR 1%)

Medidas con las mismas métricas que `visual_research.py` aplica a la competencia
(descargadas de `i.ytimg.com` el 2026-09-18):

| | luminancia media | saturación | píxeles casi negros |
|---|---|---|---|
| 26 outliers del nicho (mediana) | 0,33 | 0,35 | 42% |
| Episodios 1-4 | 0,10 – 0,21 | 0,09 – 0,42 | 75 – 86% |
| Episodio 5 | 0,26 | 0,64 | 51% |

Y el texto: "I FOUND IT", "IT'S A TRAP", "IT LIED", "IT FITS?". En el feed la
miniatura se lee antes que el título, y ninguna de esas frases dice de qué va.
Cuatro de cinco eran un objeto oscuro flotando en negro con un pronombre.

### 2. Gancho: habla del canal, no del espectador

Ep. 1 abre con *"This channel has zero videos and zero subscribers"* sobre una
captura de YouTube Studio vacía. Ep. 2 abre con *"Last video I built…"*. Un
espectador nuevo (el 96,6%) no tiene ningún motivo para seguir.

### 3. Ritmo: 15 segundos mirando la misma imagen

Mediana de 15,5 s por escena en ep. 1 (78 escenas; 43 pasan de 15 s). A los 40 s
del vídeo 1 hay una sola línea de texto centrada en negro durante 20 s, con voz
sintética. Es la definición de "diapositiva leída".

### 4. Duración: 20 minutos para un canal de 0 suscriptores

La estrategia fijó 20–30 min porque los outliers del nicho duran 28 min. Pero esos
los hacen canales con cara, pantalla grabada y voz humana. Con voz sintética y
planos fijos, 4 min retuvo 22,6% y 20 min retuvo 5,6%.

## Qué cambia (esta rama)

| Archivo | Cambio | Ataca |
|---|---|---|
| `src/facelessyt/video/lint.py` (nuevo) | Reglas de gancho y ritmo con números con nombre: primera escena ≤ 30 palabras y con payoff; sin "this channel / last video / subscribe" en las 2 primeras; ≥ 3 visuales distintos en 30 s; ninguna escena > 55 palabras; ≤ 8 min salvo `allow_long` | retención |
| `src/facelessyt/video/__main__.py` | `check` ejecuta el lint; `render` se niega si hay errores (`--force` para saltarlo); `--music`, `--no-motion`, `--no-transitions` | retención |
| `src/facelessyt/video/assemble.py` | Zoom lento alternado en cada escena (`zoompan`), fundido de 0,25 s entre escenas (`xfade`/`acrossfade`), música de fondo a −26 dB (`MUSIC_PATH` o `--music`); capítulos descuentan los fundidos | retención |
| `src/facelessyt/video/voice.py` | `PIPER_LENGTH_SCALE=0.85` y `PIPER_SENTENCE_SILENCE=0.1` (medido en el contenedor: ~176 → ~185-200 wpm) | ritmo |
| `src/facelessyt/packaging.py` (nuevo) | Lint de título (≤ 60, payoff en los primeros 40, no repetir "I Built an AI Agent") y de texto de miniatura (≤ 4 palabras, sin pronombre como sujeto, con referente, no repetir el título); auditoría de imagen con los umbrales de los outliers (luminancia ≥ 0,22, saturación ≥ 0,20, negro ≤ 60%) | CTR |
| `src/facelessyt/video/thumbnail.py` | `render_bold()`: panel de color con la cifra + titular grande; pasa la auditoría por construcción | CTR |
| `src/facelessyt/cli.py` | `facelessyt packaging` (mide antes de producir); `upload` corre el gate y **no sube** si falla; `--publish-at` | CTR, operación |
| `src/facelessyt/upload.py` | `publish_at`: sube privado con `status.publishAt`; YouTube publica solo a esa hora | operación |
| `tools/produce_episode.ps1` | lint → miniatura → gate → render Docker → subida programada, un comando | operación |
| `tools/weekly_diagnose.ps1` | `diagnose` + `track` semanal, registrable en el Programador de tareas | medición |
| `tests/test_retention_rules.py` | 20 tests sobre todo lo anterior, sin red ni ffmpeg | — |

Los guiones 01 y 02 **no pasan** el lint nuevo (29 y 25 errores): eso es lo esperado,
son los vídeos que fallaron. El lint no se puede ejecutar sobre el ep. 5 porque usa
otro formato (`cues`); sus reglas equivalentes están en `production/05-…/build_package.py`.

## Lo que el código no arregla

- **La voz.** Piper Lessac es reconociblemente sintética y plana. El pipeline ya
  soporta ElevenLabs (`ELEVENLABS_API_KEY` + `ELEVENLABS_VOICE_ID`, `--engine
  elevenlabs`); a 4-6 min por vídeo, 8 vídeos/mes caben en el plan de 5 $/mes
  (30k caracteres). Es la única compra que rompe la regla de "cero gasto" y creo
  que merece la pena probarla en dos vídeos y comparar retención a 30 s.
- **El ángulo.** El lint impide el gancho malo; no escribe el bueno. Las reglas
  para escribirlo, en formato prompt para usar con cualquier LLM, están en
  [docs/prompts/hook-packaging.md](prompts/hook-packaging.md).
- **Miniaturas hechas fuera.** `render_bold` es una plantilla de emergencia que
  pasa los umbrales. Una miniatura generada con imagen sigue siendo mejor si pasa
  `facelessyt packaging --thumbnail`. El gate no distingue el origen.

## Cómo saber si ha funcionado

Con 8 vídeos nuevos (4 semanas a 2/semana), `tools/weekly_diagnose.ps1`:

| Métrica | Ahora | Objetivo a 4 semanas | Si no llega |
|---|---|---|---|
| CTR | 1,0% | > 3% | cambiar de plantilla de miniatura, no de reglas |
| Retención a 30 s | (sin dato; AVD 0:55) | > 50% | probar voz humana/ElevenLabs |
| Retención media | 5-22% | > 30% | acortar a 3-4 min |

Si las tres suben y las views no, entonces sí toca hablar del nicho.
