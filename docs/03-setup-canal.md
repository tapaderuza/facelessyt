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

## 6. OAuth: el paso que hay que hacer una vez

Ya está configurado (`credentials.json` en la raíz, ignorado por git). Falta
autorizar, y Google bloquea con `403 access_denied` hasta que tu cuenta esté en
la lista de usuarios de prueba:

**Google Auth Platform → Audience → Test users → Add users** → el correo dueño
del canal → Save.

Después:

```bash
python -m facelessyt auth
```

Verás un aviso de "app no verificada": Avanzado → Ir a Outlier Engineering. Es
esperado. La verificación de Google solo se exige para autorizar a terceros, y
aquí el único usuario eres tú.

### Sobre la caducidad de 7 días

En modo Testing, Google caduca los refresh tokens a la semana. Merece la pena
saber a qué afecta y a qué no:

| Comando | Autenticación | Le afecta la caducidad |
|---|---|---|
| `mine` | clave de API | no |
| `check` | clave de API | no |
| `track` | clave de API | **no** |
| `upload` | OAuth | sí |
| `diagnose` | OAuth | sí |

La métrica de corte de los 90 días va con la clave de API, así que sigue
recogiendo datos aunque el token OAuth haya caducado. Lo único que pasa es que
antes de un `upload` o un `diagnose` puede tocar repetir `auth`. Molesto, no
grave.

Pasar a producción evitaría la caducidad, pero exige URL de homepage y de
política de privacidad. Para un solo usuario no compensa.

## 7. Cuando ya está autorizado

Comprueba también que esté habilitada la **YouTube Analytics API** en el mismo
proyecto (la Data API ya lo está). Sin ella, `auth` y `upload` funcionan pero
`diagnose` devuelve un 403 al pedir el informe.

```bash
python -m facelessyt upload --video data/video/01-outlier-agent-final.mp4 --title "I Built an AI Agent That Picks My YouTube Videos For Me" --thumbnail data/video/thumbnail-01.png --tags "youtube algorithm,youtube api,python tutorial,content strategy,ai automation"
```

Sube **siempre como privado**, a propósito: publicar en el canal es una decisión
tuya después de ver el vídeo entero, no algo que un script deba poder disparar.

Y a las 48 horas de publicar, lo que de verdad importa:

```bash
python -m facelessyt diagnose
```

Eso responde a la pregunta que las views no contestan: si el vídeo no funciona,
¿es el packaging, es el gancho, o es el nicho? Los umbrales salen de
`docs/00-estrategia.md` y el veredicto los aplica en ese orden.
