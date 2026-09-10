# Configuración del canal — Outlier Engineering

Canal: https://www.youtube.com/channel/UClTkb79KeKvDpybQWFDMWXA
Handle: `@outlierengineering` · ID: `UClTkb79KeKvDpybQWFDMWXA`

> **Lo que no puedo hacer yo.** Subir el avatar, el banner o el vídeo requiere
> OAuth con tu cuenta de Google, y eso son credenciales tuyas que tienes que
> generar. Los ficheros están generados y listos; subirlos son cinco minutos en
> YouTube Studio. Si prefieres automatizarlo, mira la última sección.

## 1. Avatar

Fichero: `data/branding/avatar.png` (800×800)

YouTube Studio → Personalización → Imagen de perfil → Subir.

El motivo es una fila de puntos apagados y uno verde disparado hacia arriba:
un outlier, literal. Está comprobado a 48px (`avatar-48px.png`), que es como se
ve junto a un comentario. Si no se distinguiera ahí, no valdría.

## 2. Banner

Fichero: `data/branding/banner.png` (2560×1440)

YouTube Studio → Personalización → Imagen de banner → Subir.

Solo se ve siempre un rectángulo central de 1546×423 — el resto lo recorta cada
dispositivo a su manera. Todo lo legible está dentro de esa zona; puedes
comprobarlo en `banner-safe-area.png`, que es exactamente lo que verá alguien
desde el móvil.

## 3. Descripción del canal

```
I find YouTube topics that actually have demand by scoring every video against
its own channel's median — then I build whatever the data points at, on camera,
with the code.

No keyword tools. No guessing. The tool is free and open source.

github.com/tapaderuza/facelessyt
```

## 4. Metadata del vídeo 1

**Título:** `I Built an AI Agent That Picks My YouTube Videos For Me`

**Miniatura:** `data/video/thumbnail-01.png`

**Capítulos:** en `data/video/01-outlier-agent/chapters.txt` — se generan con los
tiempos reales del montaje, así que si se re-renderiza el vídeo hay que volver a
copiarlos.

**Descripción:** ver `scripts/01-outlier-agent.md`, sección Packaging.

**Etiquetas sugeridas:**
```
youtube algorithm, youtube analytics, python tutorial, youtube api,
content strategy, ai automation, data analysis, faceless youtube
```

**Comentario fijado** (ponlo en los primeros 5 minutos):
> The formula is `views / that channel's median views`. That's it. Everything
> else in the video is plumbing. What topic would you run it on first?

## 5. Ajustes del canal que conviene tocar una vez

- **Marca de agua**: no la pongas todavía. Con 0 subs resta más que suma.
- **Trailer del canal**: será este mismo vídeo, una vez publicado.
- **Idioma del canal**: inglés. Afecta a quién se lo recomienda YouTube.
- **Palabras clave del canal**: las mismas etiquetas de arriba.
- **Monetización**: no está disponible hasta 1.000 subs y 4.000 horas. No pierdas
  tiempo mirándolo hasta que el tracker diga que se ha pasado el corte.

## 6. Si quieres que lo suba yo automáticamente

Necesito credenciales OAuth. En el **mismo** proyecto de Google Cloud donde
sacaste la clave de API:

1. Habilita **YouTube Analytics API** (la Data API ya está)
2. Pantalla de consentimiento OAuth → **Externo** → añádete como usuario de prueba
3. Credenciales → Crear → **ID de cliente de OAuth** → **Aplicación de escritorio**
4. Descarga el JSON como `D:\FacelessYT\credentials.json` (ya está en `.gitignore`)

Con eso construyo la subida automática (vídeo, miniatura, capítulos y descripción
en una sola orden) y además el módulo de CTR y retención, que usa el mismo OAuth
y es lo que hoy nos falta para diagnosticar por qué un vídeo funciona o no.
