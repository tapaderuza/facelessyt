"""Reglas de gancho y ritmo que un guion tiene que cumplir antes de renderizarse.

Vienen de los datos de los cinco primeros videos (2026-09-18), no de una guia:

  - Duracion media vista: 0:55. El video de 20 min retuvo el 5,6%; el de 4 min,
    el 22,6%. La gente se va en el primer minuto, asi que el primer minuto es
    lo unico que se puede arreglar hoy.
  - Mediana de 15 s por escena con una imagen fija. 43 de 78 escenas del
    video 1 pasaban de 15 s sin que cambiara nada en pantalla.
  - El video 1 abria con "This channel has zero videos and zero subscribers":
    hablaba del canal, no del espectador.

Cada regla es un numero con nombre, para poder discutirlo y cambiarlo cuando
haya datos nuevos. `check` las ejecuta y se niega a renderizar si alguna
falla, salvo que el guion declare explicitamente la excepcion.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 190 palabras/minuto: medido sobre un render real de Piper (ver __main__.py).
WPM = 190

# Gancho: lo que pasa antes de que el espectador decida quedarse.
HOOK_FIRST_SCENE_MAX_WORDS = 30   # ~9 s. La primera frase promete; no explica.
HOOK_WINDOW_WORDS = 95            # ~30 s: la ventana que mide YouTube.
HOOK_MIN_VISUAL_CHANGES = 3       # visuales distintos dentro de esa ventana.

# Ritmo del cuerpo. 55 palabras son ~17 s mirando la misma imagen.
SCENE_MAX_WORDS = 55

# Duracion. Los outliers del nicho duran 28 min, pero los hacen canales con
# cara y grabacion de pantalla. Con voz sintetica y planos fijos, el dato
# propio dice que 4 min retiene 4x mas que 20. Hasta que la retencion media
# pase del 40%, no se hacen videos largos.
MAX_MINUTES_DEFAULT = 8

# Frases que hablan del canal o del formato en vez del espectador. Si aparecen
# en las dos primeras escenas, el gancho esta perdido.
BANNED_OPENERS = (
    "this channel",
    "subscriber",
    "hello",
    "hi everyone",
    "hey guys",
    "welcome",
    "in this video",
    "in today's video",
    "today we",
    "today i",
    "last video",
    "last time",
    "my name is",
    "before we start",
    "let me introduce",
)

# Señales de que la primera escena enseña algo concreto: un numero, una orden
# de mirar, o el espectador como sujeto.
PAYOFF_PATTERN = re.compile(
    r"\d|\b(watch|look|here's|here is|this is|you|your)\b", re.IGNORECASE
)


@dataclass(frozen=True)
class Issue:
    level: str      # "error" | "warn"
    rule: str
    scene_id: str
    message: str

    def __str__(self) -> str:
        tag = "ERROR" if self.level == "error" else "AVISO"
        return f"  {tag:5} {self.rule:18} {self.scene_id:16} {self.message}"


def _words(scene: dict) -> int:
    return len(scene.get("narration", "").split())


def _text(scene: dict) -> str:
    return " ".join(scene.get("narration", "").split()).lower()


def _visual_key(scene: dict) -> str:
    visual = scene.get("visual", {}) or {}
    return f"{visual.get('type', '')}:{visual.get('content', '')}"


def estimate_minutes(scenes: list[dict]) -> float:
    words = sum(_words(s) for s in scenes)
    holds = sum(float(s.get("hold", 0.5)) for s in scenes)
    return words / WPM + holds / 60


def lint_script(spec: dict) -> list[Issue]:
    """Devuelve los problemas del guion. Lista vacia = se puede renderizar."""
    scenes: list[dict] = spec.get("scenes", [])
    video: dict = spec.get("video", {}) or {}
    issues: list[Issue] = []
    if not scenes:
        return [Issue("error", "empty", "-", "el guion no tiene escenas")]

    first = scenes[0]
    first_id = str(first.get("id", "?"))

    # --- Gancho -----------------------------------------------------------
    if _words(first) > HOOK_FIRST_SCENE_MAX_WORDS:
        issues.append(Issue(
            "error", "hook-length", first_id,
            f"{_words(first)} palabras en la primera escena; maximo "
            f"{HOOK_FIRST_SCENE_MAX_WORDS} (~{HOOK_FIRST_SCENE_MAX_WORDS * 60 // WPM} s). "
            "La primera frase promete, no explica.",
        ))

    if not PAYOFF_PATTERN.search(first.get("narration", "")):
        issues.append(Issue(
            "error", "hook-payoff", first_id,
            "la primera escena no muestra nada concreto: mete un numero, "
            "'watch this', o al espectador ('you') como sujeto.",
        ))

    for scene in scenes[:2]:
        text = _text(scene)
        hits = [p for p in BANNED_OPENERS if p in text]
        if hits:
            issues.append(Issue(
                "error", "hook-self-talk", str(scene.get("id", "?")),
                f"habla del canal o del formato ({', '.join(repr(h) for h in hits)}) "
                "en vez de lo que gana quien mira.",
            ))

    # Ventana de 30 s: cuantos visuales distintos ve el espectador.
    window_words, window_visuals = 0, []
    for scene in scenes:
        window_visuals.append(_visual_key(scene))
        window_words += _words(scene)
        if window_words >= HOOK_WINDOW_WORDS:
            break
    distinct = len(set(window_visuals))
    if distinct < HOOK_MIN_VISUAL_CHANGES:
        issues.append(Issue(
            "error", "hook-static", first_id,
            f"solo {distinct} visual(es) distinto(s) en los primeros ~30 s; "
            f"minimo {HOOK_MIN_VISUAL_CHANGES}. Parte la escena o cambia el visual.",
        ))

    # --- Ritmo del cuerpo ---------------------------------------------------
    for scene in scenes:
        n = _words(scene)
        if n > SCENE_MAX_WORDS:
            issues.append(Issue(
                "error", "scene-too-long", str(scene.get("id", "?")),
                f"{n} palabras (~{n * 60 // WPM} s) sobre una sola imagen; "
                f"maximo {SCENE_MAX_WORDS}. Partela en dos con visuales distintos.",
            ))

    # Dos escenas seguidas con el mismo visual es una escena larga disfrazada.
    for prev, cur in zip(scenes, scenes[1:]):
        if _visual_key(prev) == _visual_key(cur) and _words(prev) + _words(cur) > SCENE_MAX_WORDS:
            issues.append(Issue(
                "warn", "same-visual-twice", str(cur.get("id", "?")),
                f"repite el visual de '{prev.get('id')}'; juntas suman "
                f"{_words(prev) + _words(cur)} palabras sin cambio en pantalla.",
            ))

    # --- Duracion -----------------------------------------------------------
    minutes = estimate_minutes(scenes)
    max_minutes = float(video.get("max_minutes", MAX_MINUTES_DEFAULT))
    if minutes > max_minutes and not video.get("allow_long"):
        issues.append(Issue(
            "error", "too-long", "-",
            f"~{minutes:.1f} min estimados; maximo {max_minutes:g}. "
            "Corta, o declara 'allow_long: true' en video: si tienes un motivo.",
        ))

    return issues


def has_errors(issues: list[Issue]) -> bool:
    return any(i.level == "error" for i in issues)
