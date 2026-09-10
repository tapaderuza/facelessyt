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


def render_trend(out_path: Path, *, headline: str = "IT'S DYING",
                 sub: str = "and I found out before I filmed") -> Path:
    """Miniatura de curva: sube, gira y cae.

    La del video 1 era un numero grande. Correcto pero pasivo: informa y no
    genera pregunta. Una curva que se desploma la genera sola, porque el ojo
    sigue la linea hasta el final antes de leer nada.
    """
    img = Image.new("RGB", (TW, TH), BG)
    draw = ImageDraw.Draw(img)

    # Rejilla tenue: da sensacion de grafico sin competir por atencion.
    for gy in range(140, TH - 90, 90):
        draw.line([(60, gy), (770, gy)], fill=(30, 36, 44), width=2)

    # La curva. Sube fuerte y se desploma al final.
    puntos_sube = [(80, 570), (200, 490), (320, 400), (430, 265), (520, 180)]
    puntos_cae = [(520, 180), (600, 260), (660, 410), (710, 560), (750, 650)]

    draw.line(puntos_sube, fill=GREEN, width=16, joint="curve")
    draw.line(puntos_cae, fill=(248, 81, 73), width=16, joint="curve")

    # Punto de inflexion, marcado. Es donde el ojo se para.
    px, py = 520, 180
    draw.ellipse([px - 20, py - 20, px + 20, py + 20], fill=BG, outline=FG, width=6)

    # Bloque de texto a la derecha. El ancho disponible se mide, no se supone:
    # la primera version puso una coordenada a ojo y "IT'S DYING" se salia del
    # lienzo, dejando visible solo "IT'S".
    TEXT_X = 790
    ANCHO = TW - TEXT_X - 50

    def envolver(texto: str, font) -> list[str]:
        lineas, cur = [], ""
        for palabra in texto.split():
            probe = f"{cur} {palabra}".strip()
            if draw.textlength(probe, font=font) > ANCHO and cur:
                lineas.append(cur)
                cur = palabra
            else:
                cur = probe
        lineas.append(cur)
        return lineas

    # Titular: el tamano mas grande que quepa, probando hacia abajo.
    for tam in (108, 96, 84, 72, 62):
        font_h = _font(tam, bold=True)
        lineas_h = envolver(headline, font_h)
        if len(lineas_h) <= 2 and all(
            draw.textlength(ln, font=font_h) <= ANCHO for ln in lineas_h
        ):
            break

    alto_h = len(lineas_h) * (tam + 10)
    y = (TH - alto_h) / 2 - 40
    for ln in lineas_h:
        draw.text((TEXT_X, y), ln, font=font_h, fill=FG)
        y += tam + 10

    font_s = _font(32)
    y += 18
    for ln in envolver(sub, font_s):
        draw.text((TEXT_X, y), ln, font=font_s, fill=DIM)
        y += 42

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path
