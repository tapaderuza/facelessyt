# Lanzamiento — dónde publicar y qué escribir

Objetivo: llevar gente del nicho exacto al repo, y del repo al vídeo. No views
sueltas: gente que tiene el problema que resuelve la herramienta.

**Regla que atraviesa todo esto:** el enlace principal es siempre el repo, nunca
el vídeo. Un enlace a YouTube se lee como autopromoción y se entierra. El repo es
algo que la gente puede ejecutar, y eso cambia cómo lo reciben.

---

## 1. Hacker News — Show HN

El mejor encaje de los tres: herramienta libre, técnica, con un hallazgo real.

**Enlace:** `https://github.com/tapaderuza/facelessyt`

**Título** (máx. 80 caracteres, sin superlativos, sin signos de exclamación):

```
Show HN: Find YouTube topics with demand by scoring videos against channel median
```

**Primer comentario** (se publica nada más enviar, desde tu propia cuenta):

```
Author here.

I wanted to know whether a video topic had demand before spending fifteen hours
making the video. Keyword tools measure search volume, but most YouTube views
come from recommendations, not search, so that number answers a question I
wasn't asking.

What I ended up with is one line:

    outlier_score = video views / that channel's median views

Dividing by the channel's own median cancels out channel size, so a 64k-sub
channel and a 2M-sub channel become directly comparable. What's left is a
measure of the topic rather than the audience.

Two things that turned out to matter more than the formula:

- Median, not mean. One viral video pulls a mean up so hard that nothing after
  it ever registers as an outlier again.
- Excluding Shorts from the baseline. They have a completely different view
  profile, and mixing them in makes every long-form video look like a flop.

I ran it across 12 channels and 720 videos. It cost 60 units of the 10,000
free daily API quota, because it never calls search (search is 100 units per
call; walking the uploads playlist is 1 unit per 50 videos).

Two findings I didn't expect: channels under 250k subscribers produce
higher-scoring outliers than large ones, and the median outlier in the niche I
tested runs 28 minutes, which is roughly double what conventional advice says.

MIT, runs on the free API tier, and there's a Docker image if you'd rather not
install Python. Happy to hear where the methodology breaks down - the thing I'm
least sure about is the seven-day maturity window.
```

**Cuándo:** martes a jueves, 8:00–10:00 hora del Este de EE. UU. (14:00–16:00 en
España). Es cuando la portada se mueve.

**Lo que NO se hace nunca en HN:** pedir upvotes, comentar desde otra cuenta,
responder a la defensiva. Si alguien dice que el método es basura, la respuesta
buena es "puede ser, ¿dónde lo ves flojo?". Esa conversación es la que atrae más
gente que el post.

---

## 2. r/Python — flair "Showcase"

Público técnico grande y receptivo a herramientas libres. Lee las reglas de la
barra lateral antes: exigen flair y castigan los posts sin sustancia.

**Título:**

```
I scored 720 YouTube videos against their own channel's median to find which topics actually have demand
```

**Cuerpo:**

```
I kept picking video topics on instinct and then wondering why some did nothing.
Keyword tools measure search volume, but YouTube is a recommendation engine, so
that number wasn't answering my question.

The whole idea is one division:

    outlier_score = video views / that channel's median views

Because you divide by the channel's own median, channel size cancels out. A
video with 400k views on a channel that averages a million underperformed. A
video with 97k views on a 64k-subscriber channel beat its own baseline seven
times over, which means the topic pulled in an audience that wasn't already
there. Raw view count can't tell those two apart.

Implementation notes that might be useful even if you don't care about YouTube:

- The Data API runs on a 10,000 unit daily quota, and search costs 100 units per
  call. Walking a channel's uploads playlist costs 1 unit per 50 videos, so the
  whole run cost 60 units.
- Median rather than mean, because one viral video otherwise destroys the
  baseline permanently.
- Shorts are excluded. Their view profile is different enough that including
  them makes every long-form video look like a failure.
- Anything younger than seven days is ignored, in both the baseline and the
  scoring.

Stack is just requests, PyYAML and rich. Tests run without network access.
There's a Docker image, and containerising it actually surfaced a real bug: I
was resolving the project root by walking up two directories from __file__,
which is correct for a cloned repo and completely wrong once the package is
installed in site-packages.

Code: https://github.com/tapaderuza/facelessyt

Happy to take criticism on the methodology.
```

---

## 3. r/SideProject

Más tolerante con la autopromoción, pero premia el número concreto.

**Título:**

```
I built a tool that finds which YouTube topics have proven demand - found 26 in one run
```

**Cuerpo:** el mismo de r/Python, recortando la parte de implementación a dos
líneas. Aquí interesa el resultado, no el código.

---

## 4. Dónde NO publicar

**r/NewTubers, r/youtubers, r/SmallYTChannels.** Son el público más obvio y la
peor idea. Tienen reglas duras contra autopromoción y hilos dedicados donde este
post moriría enterrado. Se puede participar ahí, pero respondiendo a preguntas
de otros durante semanas, no soltando un enlace.

**r/dataisbeautiful.** Exige flair OC y una visualización como pieza principal.
El post iría a moderación y de ahí a ninguna parte.

---

## Antes de publicar: dos avisos

### La cuenta de Reddit

Muchos subreddits auto-eliminan posts de cuentas con poco karma o pocos días.
Si tu cuenta es nueva, el post desaparece sin decírtelo: te aparece publicado a
ti y a nadie más. Compruébalo abriéndolo en una ventana de incógnito unos
minutos después.

### El vídeo está narrado con voz sintética

Esto importa y conviene decidirlo antes, no improvisar cuando salga.

Hacker News en particular es hostil al contenido generado con IA. El repo, los
datos y el análisis son trabajo real y aguantan cualquier escrutinio, así que
lidera con eso. Pero si alguien pregunta por la narración del vídeo, la única
respuesta que funciona es la directa: sí, es TTS, el código y los datos no.

Intentar disimularlo sería mucho peor que el hecho en sí, y en una comunidad así
se detecta rápido.

---

## Orden y ritmo

No los publiques todos el mismo día. Si uno funciona, querrás tiempo para
responder comentarios, y responder bien es lo que convierte.

1. **Día 1** — Show HN. Es el que más tráfico cualificado da si entra.
2. **Día 3** — r/Python.
3. **Día 5** — r/SideProject.

Entre medias, responde a todo. En las primeras dos horas de un post, contestar
rápido es lo que decide si sigue subiendo.

## Qué medir

A las 48 h del primer post, `diagnose` te dirá el CTR y la retención. Pero
ojo con leerlo mal: el tráfico que venga de HN o Reddit **no pasa por miniatura**,
así que hinchará las views sin tocar el CTR de las impresiones de YouTube.

Mira las dos fuentes por separado en Studio → Analytics → Fuentes de tráfico.
Lo que dice si el canal funciona es el tráfico de YouTube, no el referido.
