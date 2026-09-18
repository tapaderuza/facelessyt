# Playbook por vídeo

Objetivo: **4 horas de trabajo por vídeo**, de las cuales solo ~1h es tuya.

## 0. Selección de tema (automatizado — `miner`)
No se elige tema por intuición. Se elige por **outlier**: un vídeo que rindió muy por encima
de la media de su propio canal es prueba de que el tema tiene demanda, independientemente del
tamaño del canal. El miner encuentra esos vídeos en tu nicho.

Regla: **no se produce nada con outlier score < 3.**

## 1. Ángulo (TÚ — 20 min)
Coges el tema validado y le pones tu prueba. El outlier dice *de qué*, tú decides *cómo*.
Mal: "Top 5 AI automation tools". Bien: "I ran the 5 top AI automation tools on the same
real task — here's what broke".

## 2. Packaging: título + miniatura (TÚ — 30 min)
Se escribe **antes** del guion. Si no consigues un título que tú mismo clicarías, el tema muere aquí.
- Título: ≤ 60 caracteres, el resultado o el número en los primeros 40, sin repetir
  el arranque de otro vídeo del canal.
- Miniatura: 2-4 palabras que **nombran algo** (no "IT LIED"), un panel de color, y
  luminancia/saturación al nivel de los outliers del nicho. Se mide, no se opina:

```bash
.venv/Scripts/python.exe -m facelessyt packaging --title "..." --thumb-text "..." --thumbnail miniatura.jpg
```

`upload` ejecuta el mismo gate y no sube si falla. Por qué: [docs/09](09-diagnostico-2026-09-18.md).
Prompts para escribirlo: [docs/prompts/hook-packaging.md](prompts/hook-packaging.md).

## 3. Guion (asistido — 45 min)
Estructura fija:
- **0–10s** el resultado, visible. ≤ 30 palabras. Sin intro, sin "this channel", sin "last video".
- **10–30s** la contradicción y qué va a poder hacer quien mira. Tres visuales distintos.
- **cuerpo**: el build/la demo. Ninguna escena > 55 palabras sobre la misma imagen.
- **cierre**: resultado + CTA único.

`facelessyt.video check` aplica estas reglas y `render` no arranca si fallan
(`--force` para saltarlo a sabiendas). Constantes en `src/facelessyt/video/lint.py`.

## 4. Voz (automatizado)
TTS. Una única voz consistente para todo el canal — la voz es la marca.

## 5. Montaje (automatizado)
Cada escena lleva zoom lento, las escenas se encadenan con fundido y hay música de
fondo si `MUSIC_PATH` apunta a un loop. Un plano fijo de 15 s con voz sintética es
lo que retuvo el 5%; ya no se genera.

## 6. Publicación (automatizado — `upload --publish-at`)
Se sube privado con hora de publicación; YouTube lo hace público solo. Hasta esa
hora se puede retirar. Todo el episodio en un comando: `tools/produce_episode.ps1`.

## 7. Medición (automatizado — `tracker`)
Se registra a 24h, 7d y 30d. La decisión del día 90 sale de aquí.

---

## Frecuencia
2 vídeos/semana, mismo día y hora. Duración objetivo **4–8 min** hasta que la retención
media pase del 40%. Los outliers del nicho duran 28 min (docs/02-hallazgos), pero los
hacen canales con cara y voz humana; con voz sintética y planos fijos, 4 min retuvo
4x más que 20 (docs/09). La consistencia importa más que el volumen.
Antes de subir el vídeo 1, ten 4 grabados. Sin colchón, la frecuencia se rompe en la semana 3.
