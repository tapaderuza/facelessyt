# Episode 05 — producción audiovisual

Este documento describe la fase de producción autorizada después de aprobar la
preproducción. `GUION.md`, `lab.html` y `render-spec.json` conservan el reloj
editorial de 240 s; el máster usa exclusivamente las duraciones medidas de Piper.

## Estado verificado — 2026-09-13

Máster generado: `data/video/05-worker-bottleneck/05-worker-bottleneck-final.mp4`.
Duración: **230,933333 s**, 6.928 frames, 14.618.995 bytes. Cuenta atrás:
**123,800–126,800 s**, exactamente 90 frames. Ocho capítulos y captions medidos.
SHA-256: `c7db0a7b8e76681bf3d0a2d3a701ffed868c68e2b4110701a8f63d9303bde612`.

- 68 tests unittest y 17 tests core: pasan.
- Animatic anterior: 13 aserciones, pasa. Canvas editorial: 45.167 aserciones
  sobre 7.200 frames, pasa. Retimado: 6.928 frames y 90 de countdown, pasa.
- Render nativo de todas las escenas: pasa. Se corrigió la sustitución de la
  fuente monospace por serif, fijando DejaVu Sans Mono antes de codificar.
- Máster: **25 comprobaciones de vídeo pasan**, incluyendo decode completo,
  A/V, capítulos, voz preservada, hashes, ticks, silencios y movimiento codificado.
- Audio codificado: **−16,11 LUFS**, pico verdadero **−4,15 dBTP**; sin intervalos
  inesperados de silencio superiores a 2 s. ROI muestreada a 10 fps: máximo
  sin cambio detectable 0,8 s; se contrasta con la firma semántica de fuente.
- Revisión visual: contacto de las ocho escenas, 3/2/1 y cola tras reanudación;
  ampliaciones de la cola y seguimiento de J04. Captions de producción a 42 px.
  Rótulos auxiliares pequeños requieren pantalla grande o pausa; no se certifica
  legibilidad universal en móvil ni regresión visual sin baseline.
- ASR local del MP4 completo contrastado con el texto: conflicto, cifras y
  resolución conservados. El reconocedor comete errores en algunas palabras
  (por ejemplo, “widened”) y sus timestamps no son alineación de voz. La
  sincronización procede del PCM medido, no del ASR. No se afirma escucha humana
  integral ni certificación audiovisual subjetiva.
- Preflight YouTube de solo lectura: canal autorizado Outlier Engineering,
  `UClTkb79KeKvDpybQWFDMWXA`; no duplicado del Episodio 05 en la consulta realizada.

**Publicado y verificado en HD:** [Episodio 05](https://www.youtube.com/watch?v=eqO9IN3eGPI).
YouTube confirma `privacyStatus: public`, `uploadStatus: processed`,
`processingStatus: succeeded`, `definition: hd`, duración `PT3M51S` y miniatura
personalizada. Título y descripción —incluidos los ocho capítulos— coinciden con
los activos locales. Publicado a las `2026-09-13T15:56:24Z` en el canal autorizado.

El JPG externo original no apareció. El usuario autorizó generar uno nuevo con la
herramienta integrada `image_gen`: [miniatura](assets/thumbnail.jpg),
[prompt](assets/THUMBNAIL-PROMPT.md) y [procedencia](assets/thumbnail-provenance.json).
Se revisaron el PNG, el JPG convertido y la miniatura servida por YouTube. No se
usó ningún SVG, placeholder ni miniatura de otro episodio. El JPG es 1672×941,
420.544 bytes. La descripción declara su origen conceptual generado por IA.

La comprobación final completa da `technical_pass: true`: **26 controles pasan**,
incluida la miniatura. El anterior `video-qa.json` conserva su alcance sin miniatura
y no es el recibo final. Los informes y metadatos finales se incluyen en `release/`;
el MP4 y el resto de artefactos audiovisuales permanecen bajo `data/`, ignorado por Git.

Recibos locales: `render-qa.json`, `visual-review.json`, `upload-receipt.json`,
`youtube-status.json`, `video-qa.json`, `motion-qa.json`, `timings.json`,
`asr-review.json`, `encoded-contact-sheet.jpg`, `chapters.txt`, `description.txt`
y `captions.en.srt` dentro del directorio del máster.

## Render reproducible

Desde `D:\FacelessYT`, con la imagen base `facelessyt-video` disponible:

```powershell
docker build -f Dockerfile.episode05 -t facelessyt-episode05 .
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' facelessyt-episode05 --audio-only
node production/05-worker-bottleneck/test_retime.cjs
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' facelessyt-episode05 --stills
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' facelessyt-episode05
```

`produce.py` sintetiza localmente con Piper Lessac, mide el PCM de cada frase y
conserva todas las palabras. Cada cue termina en una frontera de frame a 30 fps.
`retime.cjs` mapea cada cue medido al intervalo editorial correspondiente;
`render_video.cjs` dibuja cada frame mediante el mismo `renderer.js` del laboratorio.
No se acelera el audio para forzarlo a la duración editorial.

La cuenta atrás conserva exactamente 90 frames después de terminar la pregunta.
No lleva voz; incluye tres ticks de 70 ms. Los captions siguen los límites reales
de cada WAV, no una estimación basada en caracteres. No es alineación palabra a
palabra. La velocidad de simulación rotulada también se ajusta al reloj real.

Las ocho escenas se codifican H.264, 1080p, 30 fps, yuv420p. FFmpeg concatena y
añade AAC estéreo a 48 kHz, normalización de sonoridad en dos pasadas y capítulos
derivados del montaje medido. Los artefactos se guardan en
`data/video/05-worker-bottleneck/`, excluido de Git por la política existente.

## Miniatura externa obligatoria

No hay generador de miniaturas en este pipeline. Se exige el JPG externo aprobado:

```powershell
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' facelessyt-episode05 --bundle-only --thumbnail /work/production/05-worker-bottleneck/assets/thumbnail.jpg --thumbnail-origin builtin_imagegen_raster
```

El JPG incluido se generó con `image_gen` tras autorización del usuario y se
inspeccionó después de codificarlo con FFmpeg. No procede del renderer de vídeo.
El PNG original, prompt y procedencia se conservan en `assets/`. El comando exige
JPEG real, 16:9, al menos 640 px de ancho y menos de 2 MB. Copia sin modificar sus
píxeles y registra SHA-256. No convierte un SVG ni reutiliza otro episodio.

## Controles y publicación

```powershell
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work --entrypoint python facelessyt-research -m unittest discover -s tests -v
.\.venv\Scripts\python.exe tests/test_core.py
node production/05-worker-bottleneck/test_lab.cjs
node production/05-worker-bottleneck/test_retime.cjs
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' --entrypoint python facelessyt-episode05 production/05-worker-bottleneck/verify_render.py
docker run --rm --mount 'type=bind,source=D:\FacelessYT,target=/work' -w /work --entrypoint python facelessyt-episode04qa production/05-worker-bottleneck/check_speech.py
```

Sin miniatura se puede verificar el vídeo con `verify_render.py --video-only`;
ese informe **nunca** autoriza publicar. La revisión del máster comprueba decode
completo, sincronía A/V, capítulos, sonoridad, silencios y movimiento del MP4.
El movimiento se contrasta con estados semánticos de fuente, sin aceptar que un
logo o un temblor decorativo enmascaren una simulación congelada.

Después se inspeccionan los fotogramas codificados, el reto y la transcripción
ASR completa (puede contener errores de reconocimiento), así como la miniatura.
Solo tras esa revisión se registra `visual-review.json` con `approved: true`,
`video_sha256` y `thumbnail_sha256` de los activos revisados, indicando alcance
y limitaciones. No equivale a una reproducción humana integral certificada.

```powershell
.\.venv\Scripts\python.exe production/05-worker-bottleneck/publish_episode.py
.\.venv\Scripts\python.exe production/05-worker-bottleneck/publish_episode.py --public
.\.venv\Scripts\python.exe production/05-worker-bottleneck/publish_episode.py --status
```

La primera invocación es solo lectura. `--public` verifica canal, duplicados,
informes y hashes, y aplica la autorización únicamente a este episodio. Conserva
un marcador antes de subir y el ID antes de adjuntar la miniatura: nunca repetir
la inserción a ciegas si falla una operación posterior. Un recibo existente hace
que las invocaciones siguientes consulten el vídeo conocido.

No se modifica la privacidad por defecto del resto del repositorio. No se añade
el episodio al catálogo de publicados hasta confirmar la publicación real.
