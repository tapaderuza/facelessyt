# Revelado, títulos y una voz que se cambió sola (2026-09-22)

Tres cosas: qué dicen los datos nuevos del nicho, qué cambia en el render, y un
fallo real que apareció mientras lo probaba.

## 1. Investigación: 33 outliers, dos snapshots

Segundo minado (`data/outliers-ai-automation-2026-09-22.json`), unido al del
10 de septiembre: 33 vídeos outlier únicos. Tres hipótesis sobre el título,
medidas contra el score (views del vídeo ÷ mediana de su propio canal):

| Hipótesis | Con | Sin | Veredicto |
|---|---|---|---|
| Nombra una herramienta (Claude, n8n, MLX…) | **5,17x** (n=18) | 3,72x (n=15) | señal |
| Lleva un número | 4,45x (n=12) | 4,68x (n=21) | **nada** |
| ≤ 50 caracteres | **3,31x** (n=8) | 5,08x (n=25) | señal, al revés de lo que yo creía |

Longitud de los títulos outlier: min 38, p25 52, **mediana 58**, p75 68, max 95.

Dos consecuencias, las dos en `packaging.py`:

- **`TITLE_MIN_CHARS = 45`**. Mi regla sólo miraba el máximo, y el instinto de
  "cuanto más corto, más limpio" va contra los datos. El título del vídeo 6
  ("180 Views in 28 Days. The Fix Was a Linter.", 43 caracteres) ahora lo marca.
- **`names_tool()` y `title_search_note()`**. No es un error, es un aviso: con
  un canal sin audiencia, la búsqueda es el único tráfico que no depende del
  algoritmo. El vídeo 7 recibió el 25 % de sus vistas por la búsqueda
  "elevenlabs", con 121 impresiones totales.

Es correlación, no causa: el tema y la herramienta viajan juntos, y 33 vídeos
de un solo nicho no son una muestra para presumir. Por eso son un aviso y un
mínimo, no un gate que bloquee la subida.

## 2. Revelado progresivo

El zoom lento quitó la señal de "diapositiva", pero la pantalla seguía
entregando toda la información en el primer fotograma: nada que esperar. Ahora
las líneas del terminal **aparecen según se narran**.

- `scenes.render_reveal(scene, outdir, stem)` devuelve un PNG por paso. Un paso
  = una línea con texto; las vacías son separadores.
- La maquetación se calcula **siempre con todas las líneas** y sólo se omite el
  dibujado de las que aún no tocan. Si se truncara la lista, el bloque se
  recentraría en cada paso y el texto saltaría. Hay un test que lo comprueba
  píxel a píxel: lo que dibuja un paso tiene que ser idéntico en la imagen final.
- Sólo se revelan los terminales. El texto centrado son dos o tres palabras
  grandes; aparecer por partes ahí sólo distrae.
- El revelado ocupa el 75 % del audio (`REVEAL_SHARE`); el último cuarto se
  queda la imagen completa para que se lea el remate.

Detalle que costó una tarde: el demuxer de concat de ffmpeg redondea cada
duración a la base de tiempo del stream y el error se acumula, así que los
clips salían hasta 1,2 s cortos y el remate se perdía. En vez de pelearme con
la aritmética, el listado ahora dura **de más a propósito**
(`REVEAL_TAIL_MARGIN = 1.5`) y quien corta es `-t`. Ese es el número que manda.

## 3. El fallo: la voz cambió sola

Probando el revelado lancé el render con `docker run` a mano y **olvidé pasar
`-e ELEVENLABS_API_KEY`**. Dentro del contenedor, `--engine auto` no encontró
la clave, cayó a Piper, y re-locutó los 18 planos del episodio 8 con otra voz.
Sin un aviso. El vídeo ya estaba subido con la voz buena.

El caché de `paidcache` hizo su trabajo (la huella incluye el motor, así que
detectó que el audio no servía y lo regeneró), pero regenerar en silencio es
justo lo que no quieres cuando lo que cambia es la voz del canal.

`assemble.check_engine()` lo convierte en un error con nombre:

```
No se renderiza: Este episodio esta locutado con 'elevenlabs' y ahora se usaria 'piper'.
Falta ELEVENLABS_API_KEY en el entorno del render.
Si el cambio de voz es intencionado, usa --allow-voice-change.
```

Sale antes de renderizar nada, dice qué falta, y tiene salida (`--allow-voice-change`)
para cuando el cambio sea a propósito. Cuatro tests cubren los cuatro casos.

## Lo que sigue sin saberse

El episodio 6 marca 53 % de retención media y el 7 un 55 %, pero con **3
espectadores únicos**: la mayoría de esas reproducciones son propias. Ningún
número de retención de los vídeos nuevos es fiable todavía. El dato que sí es
limpio es el alcance: 121 impresiones en 3 días. La comparación que importa es
impresiones del vídeo 8 (título con herramienta) contra esas 121.
