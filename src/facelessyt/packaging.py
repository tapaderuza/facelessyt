"""Packaging: titulo + miniatura. Lo que decide el clic antes de que exista el video.

Diagnostico del 2026-09-18 (28 dias, 5 videos): 4.200 impresiones, CTR 1,0%.
YouTube enseñaba los videos (42% browse, 34% sugeridos) y nadie clicaba. Las
miniaturas publicadas, medidas con las mismas metricas que `visual_research`
aplica a los outliers de la competencia:

                     luminancia   saturacion   pixeles casi negros
  outliers (n=26)    0,33 med.    0,35 med.    42% med.  (p75: 55%)
  episodios 1-4      0,10-0,21    0,09-0,42    75-86%
  episodio 5         0,26         0,64         51%

Cuatro de cinco miniaturas eran un objeto oscuro sobre fondo negro con dos o
tres palabras sin referente ("IT LIED", "IT FITS?", "I FOUND IT"). En el feed,
con tema oscuro, desaparecen; y el texto no dice de que va el video.

Este modulo no decide el packaging: lo mide contra esos umbrales y se niega a
subir uno que ya sabemos que no funciona.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

# --- Titulo ----------------------------------------------------------------
# Medido sobre 33 outliers del nicho (snapshots 2026-09-10 y 2026-09-22):
#   longitud   min 38   p25 52   mediana 58   p75 68   max 95
#   <= 50 caracteres  ->  score mediano 3,31x
#    > 50 caracteres  ->  score mediano 5,08x
# Asi que el limite superior se queda donde estaba (mas de 60 se corta en el
# feed), pero se avisa por abajo: un titulo de 40 caracteres no es "limpio",
# es un titulo que no ha dicho de que va.
TITLE_MAX_CHARS = 60
TITLE_MIN_CHARS = 45
# En el movil se ven ~40 caracteres antes del "...". Lo importante va delante.
TITLE_MOBILE_CHARS = 40

# Herramientas y productos que la gente busca por su nombre. En la misma
# muestra: titulo con herramienta nombrada -> score mediano 5,17x; sin ella,
# 3,72x (n=18 vs 15). Es correlacion, no causa: el tema y la herramienta van
# juntos. Pero es la unica palanca de descubrimiento que controla un canal sin
# audiencia, porque la busqueda no depende del algoritmo de recomendacion.
# El video 7 recibio el 25% de su trafico por la busqueda "elevenlabs".
KNOWN_TOOLS = (
    "claude", "claude code", "chatgpt", "gpt", "codex", "gemini", "anthropic",
    "openai", "cursor", "copilot", "n8n", "zapier", "make.com", "langchain",
    "llamaindex", "ollama", "llama", "mistral", "deepseek", "qwen", "grok",
    "mlx", "gemma", "whisper", "elevenlabs", "piper", "ffmpeg", "docker",
    "supabase", "replit", "windsurf", "notion", "obsidian", "archon",
    "playwright", "puppeteer", "pytest", "postgres", "redis", "kubernetes",
)

# --- Texto de la miniatura -------------------------------------------------
THUMB_MAX_WORDS = 4
# Palabras que no nombran nada. Un texto hecho solo de estas ("IT LIED") es
# ilegible sin el titulo, y en el feed la miniatura se lee ANTES que el titulo.
CONTENTLESS_WORDS = {
    "i", "me", "my", "we", "you", "your", "it", "its", "it's", "this", "that",
    "the", "a", "an", "is", "was", "are", "did", "do", "does", "not", "no",
    "yes", "so", "and", "or", "but", "found", "lied", "lies", "fits", "moved",
    "said", "works", "worked", "broke", "failed", "wrong", "right", "trap",
    "really", "again", "still", "now", "here", "there", "why", "how", "what",
}
PRONOUN_SUBJECTS = ("it", "it's", "its", "this", "that", "i")

# --- Imagen ----------------------------------------------------------------
# Umbrales: entre el p25 de los outliers y lo que tenian los episodios 1-4.
THUMB_MIN_LUMINANCE = 0.22    # media de gris, 0..1
THUMB_MIN_SATURATION = 0.20   # media del canal S de HSV, 0..1
THUMB_MAX_DARK_SHARE = 0.60   # fraccion de pixeles con gris < 40
THUMB_MIN_WIDTH = 1280
NEAR_BLACK = 40

_WORD = re.compile(r"[a-z0-9']+")


def _content_words(text: str) -> list[str]:
    return [w for w in _WORD.findall(text.lower()) if w not in CONTENTLESS_WORDS]


def names_tool(title: str) -> str | None:
    """La herramienta nombrada en el titulo, si la hay. Mas larga primero, para
    que 'claude code' gane a 'claude'."""
    low = title.lower()
    for tool in sorted(KNOWN_TOOLS, key=len, reverse=True):
        if re.search(rf"(?<![a-z0-9]){re.escape(tool)}(?![a-z0-9])", low):
            return tool
    return None


def lint_title(title: str) -> list[str]:
    problems = []
    if len(title) > TITLE_MAX_CHARS:
        problems.append(f"{len(title)} caracteres; maximo {TITLE_MAX_CHARS}.")
    elif len(title) < TITLE_MIN_CHARS:
        problems.append(
            f"solo {len(title)} caracteres. Los outliers del nicho estan en 58 de "
            f"mediana, y los de menos de 50 puntuan 3,3x frente a 5,1x. "
            "Corto no es limpio: te has dejado fuera la promesa o el resultado."
        )
    head = title[:TITLE_MOBILE_CHARS]
    if not re.search(r"\d", head) and not _content_words(head):
        problems.append(
            f"los primeros {TITLE_MOBILE_CHARS} caracteres (lo que se ve en movil) "
            "no dicen de que va: pon el resultado o el numero delante."
        )
    if title.lower().startswith("i built an ai agent"):
        problems.append(
            "'I Built an AI Agent...' ya se uso dos veces: en el feed todos los "
            "videos del canal parecen el mismo."
        )
    return problems


def title_search_note(title: str) -> str:
    """Aviso, no error: el titulo no nombra ninguna herramienta buscable."""
    tool = names_tool(title)
    if tool:
        return f"nombra '{tool}': esa palabra se busca, y la busqueda no depende del feed."
    return ("no nombra ninguna herramienta conocida. Con un canal sin audiencia, "
            "la busqueda es el unico trafico que no depende del algoritmo "
            "(los outliers con herramienta puntuan 5,2x frente a 3,7x).")


def lint_thumb_text(text: str, title: str = "") -> list[str]:
    """El texto de la miniatura tiene que nombrar algo y no repetir el titulo."""
    problems = []
    words = _WORD.findall(text.lower())
    if not words:
        return ["la miniatura no lleva texto."]
    if len(words) > THUMB_MAX_WORDS:
        problems.append(f"{len(words)} palabras; maximo {THUMB_MAX_WORDS} para leerse a 120 px.")
    if words[0] in PRONOUN_SUBJECTS:
        problems.append(
            f"empieza por '{words[0]}': un pronombre sin referente. "
            "Que lied? Que fits? Nombra la cosa."
        )
    if not _content_words(text) and not re.search(r"\d", text):
        problems.append(
            "ninguna palabra nombra algo concreto (numero, objeto, resultado)."
        )
    if title:
        overlap = set(_content_words(text)) & set(_content_words(title))
        content = _content_words(text)
        if content and len(overlap) == len(set(content)):
            problems.append(
                "repite el titulo palabra por palabra: titulo y miniatura tienen "
                "que decir cosas distintas (uno el que, otra el resultado)."
            )
    return problems


@dataclass
class ThumbAudit:
    path: Path
    width: int
    height: int
    luminance: float
    saturation: float
    dark_share: float
    problems: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.problems


def audit_thumbnail(path: Path) -> ThumbAudit:
    """Mide la imagen. Solo PIL: tiene que funcionar sin OpenCV ni Tesseract."""
    from PIL import Image, ImageStat

    with Image.open(path) as im:
        rgb = im.convert("RGB")
    grey = rgb.convert("L")
    hist = grey.histogram()
    total = sum(hist)
    luminance = sum(i * c for i, c in enumerate(hist)) / total / 255
    dark_share = sum(hist[:NEAR_BLACK]) / total
    saturation = ImageStat.Stat(rgb.convert("HSV")).mean[1] / 255

    audit = ThumbAudit(path, rgb.width, rgb.height, luminance, saturation, dark_share)
    if rgb.width < THUMB_MIN_WIDTH:
        audit.problems.append(f"{rgb.width} px de ancho; YouTube sirve 1280.")
    if abs(rgb.width / rgb.height - 16 / 9) > 0.02:
        audit.problems.append("no es 16:9; YouTube la recortara.")
    if luminance < THUMB_MIN_LUMINANCE:
        audit.problems.append(
            f"luminancia {luminance:.2f} < {THUMB_MIN_LUMINANCE}: demasiado oscura "
            "para el feed en tema oscuro (los outliers estan en 0,33)."
        )
    if saturation < THUMB_MIN_SATURATION:
        audit.problems.append(
            f"saturacion {saturation:.2f} < {THUMB_MIN_SATURATION}: sin color no hay "
            "nada que pare el scroll (los outliers estan en 0,35)."
        )
    if dark_share > THUMB_MAX_DARK_SHARE:
        audit.problems.append(
            f"{dark_share:.0%} de pixeles casi negros; maximo {THUMB_MAX_DARK_SHARE:.0%}. "
            "El sujeto tiene que llenar el encuadre, no flotar en negro."
        )
    return audit


def report(title: str, thumb_text: str, thumbnail: Path | None) -> tuple[list[str], ThumbAudit | None]:
    """Todo junto, para el CLI y para `upload`."""
    problems = [f"titulo: {p}" for p in lint_title(title)]
    problems += [f"texto miniatura: {p}" for p in lint_thumb_text(thumb_text, title)]
    audit = None
    if thumbnail is not None:
        audit = audit_thumbnail(thumbnail)
        problems += [f"imagen: {p}" for p in audit.problems]
    return problems, audit
