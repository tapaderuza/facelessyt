# Prompts: gancho, título y miniatura

El pipeline no usa ningún LLM: los guiones se escriben a mano en YAML. Estos prompts
son para escribirlos (con Claude, ChatGPT, lo que sea) de forma que **pasen el lint**
de `facelessyt.video check` y el gate de `facelessyt packaging` a la primera. Las
reglas del prompt son las mismas constantes de `video/lint.py` y `packaging.py`;
si cambias una, cambia la otra.

Los ejemplos "mal" son literales de los vídeos 1-5 y su CTR fue del 1%.

---

## 1. Packaging (antes del guion)

```text
You write YouTube packaging for "Outlier Engineering", an English faceless channel
about AI automation and indie software, where every video shows a real build with
real numbers. Viewers are developers and technical founders. 96% of viewers are new:
nothing may assume they know the channel.

TOPIC: <one paragraph: what was built, the one number that surprised you, what broke>

Produce 5 candidates. Each candidate = TITLE + THUMBNAIL TEXT + FIGURE.

TITLE rules:
- <= 60 characters. The payoff or the number must appear in the first 40 characters
  (that is all a phone shows).
- Must name a concrete thing (a number, a tool, a result). No pronoun-only teasers.
- Do NOT start with "I Built an AI Agent" (used twice already; the feed shows the
  channel's videos side by side and they must not look identical).
- Title and thumbnail text must say DIFFERENT things: one says what, the other says
  the result. Never repeat the same words in both.

THUMBNAIL TEXT rules:
- 2 to 4 words, readable at 120 px wide.
- Must NOT start with "it", "it's", "this", "that" or "I": the thumbnail is read
  before the title, so a pronoun has no referent.
  BAD (real, 1% CTR): "IT LIED", "IT FITS?", "I FOUND IT", "IT'S A TRAP".
  GOOD: "2x WORKERS. SAME SPEED.", "12.7x", "60 UNITS, NOT 10,000".
- At least one word must be a number, an object or a result.

FIGURE: the single number or symbol that goes huge on a colored panel next to the
text ("2x", "12.7x", "0.4%", "15 min"). If the topic has no number, find one.

Output as a table: title | thumbnail text | figure | why a stranger would click.
```

## 2. Gancho (primeras 3 escenas del YAML)

```text
Write the first three scenes of the video script in the YAML format below.
Narration is read by a synthetic voice at ~190 words per minute, so:
- Short sentences. No subordinate clauses. No acronyms without saying them.
- Every scene must have a DIFFERENT visual; something changes on screen at least
  three times in the first 30 seconds.

HARD RULES (a linter rejects the script otherwise):
- Scene 1: <= 30 words. It must contain a number, or "watch this / look / here's",
  or address the viewer as "you". It shows the result FIRST; it does not explain.
- Scenes 1-2 must not contain: "this channel", "subscriber", "hello", "welcome",
  "in this video", "today we", "last video", "last time", "my name is".
  BAD (real, 5.6% retention): "This channel has zero videos and zero subscribers."
  BAD (real, 2.6% retention): "Last video I built a tool that finds topics."
- No scene anywhere in the script may exceed 55 words (17 s on one image).
- Whole video: 4 to 8 minutes. Not 20.

Structure:
  scene 1 (<= 30 words): the result, stated as something the viewer can see now.
  scene 2: the contradiction or the cost ("it should have doubled; it didn't move").
  scene 3: what they will be able to do by the end, concretely, in one sentence.

TOPIC / NUMBERS: <paste>

Format:
  - id: hook-1
    chapter: <2-4 words>
    narration: >
      ...
    visual:
      type: terminal | text | split
      content: <key from scenes.CONTENT, or the literal text if type: text>
    hold: 0.4
```

## 3. Cuerpo (resto del guion)

```text
Continue the script. Same YAML format and the same hard rules (<= 55 words per
scene, a different visual per scene, total 4-8 minutes).

Every 45-60 seconds insert one of these, in order, so the viewer gets a reason to
stay: (a) a number they didn't expect, (b) something that broke and the fix,
(c) a "what would you guess?" question answered within 10 seconds.

Finish with ONE call to action, the repo URL, and the next video's promise in one
sentence. No "like and subscribe".
```

## Comprobar

```bash
.venv/Scripts/python.exe -m facelessyt.video check --script scripts/06-xxx.yaml
```

```bash
.venv/Scripts/python.exe -m facelessyt packaging --title "..." --thumb-text "..." --thumbnail path.jpg
```
