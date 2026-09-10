"""Identidad visual del canal: avatar y banner.

El motivo es literal: una fila de puntos apagados a la misma altura y uno verde
muy por encima. Eso es un outlier, y es lo que hace el canal. Funciona a 48px
(el avatar en los comentarios) porque no depende de leer nada.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .scenes import BG, DIM, FG, GREEN, _font

# Avatar: YouTube pide 800x800 y lo recorta en circulo.
AVATAR = 800

# Banner: se sube a 2560x1440, pero cada dispositivo recorta distinto.
# Lo unico visible SIEMPRE es un rectangulo de 1546x423 centrado. Todo lo que
# importe va ahi dentro; el resto es relleno que en movil no se ve.
BANNER_W, BANNER_H = 2560, 1440
SAFE_W, SAFE_H = 1546, 423


def _outlier_dots(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    *,
    scale: float = 1.0,
    count: int = 5,
) -> None:
    """La marca: puntos en linea y uno disparado hacia arriba."""
    gap = 74 * scale
    radius = 21 * scale
    start = cx - gap * (count - 1) / 2

    for i in range(count):
        x = start + gap * i
        draw.ellipse([x - radius, cy - radius, x + radius, cy + radius], fill=DIM)

    # El outlier: mas grande, verde, muy por encima de la linea.
    ox = start + gap * (count - 2)
    oy = cy - 155 * scale
    orad = radius * 1.65
    draw.ellipse([ox - orad, oy - orad, ox + orad, oy + orad], fill=GREEN)


def avatar(out_path: Path) -> Path:
    img = Image.new("RGB", (AVATAR, AVATAR), BG)
    draw = ImageDraw.Draw(img)
    # Desplazado hacia abajo porque el outlier ocupa la mitad superior.
    _outlier_dots(draw, AVATAR / 2, AVATAR / 2 + 130, scale=1.55, count=5)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def banner(out_path: Path, *, name: str = "OUTLIER ENGINEERING",
           tagline: str = "Find what actually works. Then build it.") -> Path:
    img = Image.new("RGB", (BANNER_W, BANNER_H), BG)
    draw = ImageDraw.Draw(img)

    safe_x = (BANNER_W - SAFE_W) / 2
    safe_y = (BANNER_H - SAFE_H) / 2

    # Marca a la izquierda de la zona segura.
    _outlier_dots(draw, safe_x + 240, safe_y + SAFE_H / 2 + 55, scale=0.95, count=5)

    # Nombre y lema, alineados a la derecha de la marca.
    text_x = safe_x + 450
    font_name = _font(96, bold=True)
    draw.text((text_x, safe_y + 130), name, font=font_name, fill=FG)

    font_tag = _font(42)
    draw.text((text_x, safe_y + 252), tagline, font=font_tag, fill=DIM)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path


def safe_area_preview(banner_path: Path) -> Path:
    """Recorta el banner a lo unico que se ve en movil.

    Si el nombre no se lee aqui, el banner esta mal por bonito que quede
    completo: la mayoria de la audiencia solo vera este recorte.
    """
    img = Image.open(banner_path)
    left = (BANNER_W - SAFE_W) // 2
    top = (BANNER_H - SAFE_H) // 2
    crop = img.crop((left, top, left + SAFE_W, top + SAFE_H))
    out = banner_path.with_name(f"{banner_path.stem}-safe-area{banner_path.suffix}")
    crop.save(out)
    return out


def avatar_small_preview(avatar_path: Path, size: int = 48) -> Path:
    """El avatar como se ve en un comentario. Si aqui no se distingue, no vale."""
    img = Image.open(avatar_path).resize((size, size), Image.LANCZOS)
    out = avatar_path.with_name(f"{avatar_path.stem}-{size}px{avatar_path.suffix}")
    img.save(out)
    return out
