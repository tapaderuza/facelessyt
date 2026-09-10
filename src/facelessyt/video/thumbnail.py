"""Miniatura del video.

Reglas que se respetan aqui, y el motivo de cada una:
  - 1280x720, que es lo que sirve YouTube.
  - Tres elementos como mucho. Mas es ruido a tamano pequeno.
  - El elemento principal ocupa ~1/3 del alto: tiene que leerse a 120px de
    ancho, que es como se ve en el movil. Si no se lee ahi, no existe.
  - Sin flechas rojas ni caras de sorpresa. El dato ES el gancho.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from .scenes import BG, DIM, FG, GREEN, _font

TW, TH = 1280, 720


def render(out_path: Path, *, number: str = "12.7x", caption: str = "I found it with code") -> Path:
    img = Image.new("RGB", (TW, TH), BG)
    draw = ImageDraw.Draw(img)

    # La composicion es en dos bandas horizontales, no en columnas: a 120px de
    # ancho las columnas se pisan y no se lee ninguna de las dos cosas.
    SPLIT = 300  # donde acaba la tabla y empieza el numero

    # 1) Banda superior: la tabla, atenuada. Da contexto, no compite.
    rows = [
        ("Score    Views   Channel", DIM, 26),
        ("-" * 34, DIM, 26),
        ("12.7x   182.3k   The AI Automators", GREEN, 30),
        ("10.5x   158.7k   Cole Medin", FG, 30),
        (" 7.7x   779.8k   Greg Isenberg", FG, 30),
    ]
    y = 46
    for text, color, size in rows:
        draw.text((64, y), text, font=_font(size), fill=color)
        y += size + 12

    # Velo uniforme sobre la tabla: baja su peso visual de golpe, sin degradados
    # que a tamano pequeno solo ensucian.
    veil = Image.new("RGBA", (TW, TH), (0, 0, 0, 0))
    ImageDraw.Draw(veil).rectangle([0, 0, TW, SPLIT], fill=(13, 17, 23, 150))
    img = Image.alpha_composite(img.convert("RGBA"), veil).convert("RGB")
    draw = ImageDraw.Draw(img)

    # Linea que separa las dos bandas.
    draw.line([(64, SPLIT), (TW - 64, SPLIT)], fill=(48, 54, 61), width=3)

    # 2) Banda inferior: el numero, centrado y sin nada detras que lo pise.
    font_num = _font(250, bold=True)
    nw = draw.textlength(number, font=font_num)
    ny = SPLIT + 40
    draw.text(((TW - nw) / 2, ny), number, font=font_num, fill=GREEN)

    # 3) La frase de contexto. Sin ella el numero no significa nada.
    font_cap = _font(46, bold=True)
    cw = draw.textlength(caption, font=font_cap)
    draw.text(((TW - cw) / 2, ny + 262), caption, font=font_cap, fill=FG)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def legibility_check(path: Path, width: int = 120) -> Path:
    """Reduce la miniatura al tamano en que se ve en el movil.

    Si el numero no se lee en esta version, la miniatura no vale, por bonita
    que quede a tamano completo.
    """
    img = Image.open(path)
    small = img.resize((width, int(width * TH / TW)), Image.LANCZOS)
    out = path.with_name(f"{path.stem}-{width}px{path.suffix}")
    small.save(out)
    return out
