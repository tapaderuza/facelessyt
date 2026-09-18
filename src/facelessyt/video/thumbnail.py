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


# ---------------------------------------------------------------------------
# Miniatura de alto contraste (2026-09-18).
#
# Las cuatro miniaturas que peor CTR dieron compartian tres cosas: fondo negro
# (75-86% de pixeles casi negros), poca saturacion, y dos palabras que no
# nombraban nada. Esta plantilla invierte las tres: un bloque de color que
# ocupa la mitad del lienzo, texto de 3-4 palabras a >= 150 px, y una franja
# con el sujeto (un numero o un objeto) para que se entienda sin el titulo.
# `packaging.audit_thumbnail` la mide con los mismos umbrales que a las demas.
# ---------------------------------------------------------------------------

AMBER = (255, 176, 0)
WHITE = (255, 255, 255)
INK = (16, 18, 24)
PANELS = {
    "amber": (255, 176, 0),
    "green": (46, 204, 113),
    "red": (231, 76, 60),
    "blue": (52, 152, 219),
}


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        probe = f"{cur} {word}".strip()
        if draw.textlength(probe, font=font) > max_width and cur:
            lines.append(cur)
            cur = word
        else:
            cur = probe
    lines.append(cur)
    return lines


def render_bold(out_path: Path, *, headline: str, figure: str, sub: str = "",
                panel: str = "amber") -> Path:
    """Panel de color a la izquierda con la cifra/objeto; titular a la derecha.

    headline : 2-4 palabras que nombran el resultado ("4 MIN > 20 MIN").
    figure   : lo que va grande en el panel de color: un numero ("12.7x"),
               un simbolo o una palabra corta. Es lo que se lee a 120 px.
    sub      : una linea pequena de contexto bajo el titular. Opcional.
    """
    color = PANELS.get(panel, AMBER)
    img = Image.new("RGB", (TW, TH), INK)
    draw = ImageDraw.Draw(img)

    # Panel de color: 46% del ancho, con un corte diagonal para que no parezca
    # una tabla. Es lo que evita el "objeto oscuro sobre negro".
    split = int(TW * 0.46)
    draw.polygon([(0, 0), (split + 70, 0), (split - 70, TH), (0, TH)], fill=color)

    # La cifra, lo mas grande que quepa en el panel.
    for size in (360, 320, 280, 240, 200, 160):
        font_fig = _font(size, bold=True)
        if draw.textlength(figure, font=font_fig) <= split - 80:
            break
    fw = draw.textlength(figure, font=font_fig)
    fh = font_fig.getbbox("Ag")[3]
    draw.text(((split - fw) / 2 - 10, (TH - fh) / 2 - 20), figure, font=font_fig, fill=INK)

    # Titular a la derecha: el mayor tamano con el que cabe en <= 3 lineas.
    text_x = split + 60
    max_w = TW - text_x - 50
    for size in (170, 150, 130, 110, 96):
        font_h = _font(size, bold=True)
        lines = _wrap(draw, headline.upper(), font_h, max_w)
        if len(lines) <= 3 and all(draw.textlength(ln, font=font_h) <= max_w for ln in lines):
            break
    # La linea de contexto tambien se envuelve: la primera version la pintaba
    # de un tiron y se salia del lienzo.
    font_s = _font(40, bold=True)
    sub_lines = _wrap(draw, sub, font_s, max_w) if sub else []
    line_h = size + 8
    block_h = len(lines) * line_h + len(sub_lines) * 50 + (8 if sub_lines else 0)
    y = (TH - block_h) / 2
    for ln in lines:
        # Sombra dura: separa el blanco del fondo aunque la imagen se comprima.
        draw.text((text_x + 6, y + 6), ln, font=font_h, fill=(0, 0, 0))
        draw.text((text_x, y), ln, font=font_h, fill=WHITE)
        y += line_h
    y += 8
    for ln in sub_lines:
        draw.text((text_x, y), ln, font=font_s, fill=color)
        y += 50

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path


def render_over_image(background: Path, out_path: Path, *, headline: str,
                      figure: str = "", panel: str = "amber") -> Path:
    """Imagen generada fuera (ChatGPT, DALL-E...) + texto puesto por codigo.

    Los generadores de imagen escriben texto de forma inconsistente y tienden
    a fondos oscuros. Aqui la imagen solo pone el objeto; el titular va en una
    banda de color solida abajo, y la cifra en un recuadro arriba a la
    izquierda. Asi el texto siempre se lee a 120 px y la auditoria de
    `packaging` mide una miniatura con color de verdad.
    """
    color = PANELS.get(panel, AMBER)
    src = Image.open(background).convert("RGB")
    # Recorte centrado a 16:9 y escala a 1280x720.
    target = TW / TH
    w, h = src.size
    if w / h > target:
        nw = int(h * target)
        src = src.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w / target)
        src = src.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    img = src.resize((TW, TH), Image.LANCZOS)
    draw = ImageDraw.Draw(img)

    # Banda inferior: 34% del alto, color solido. Es lo que sube la luminancia.
    band_top = int(TH * 0.66)
    draw.rectangle([0, band_top, TW, TH], fill=color)
    max_w = TW - 100
    for size in (120, 104, 92, 80):
        font_h = _font(size, bold=True)
        lines = _wrap(draw, headline.upper(), font_h, max_w)
        if len(lines) <= 2 and all(draw.textlength(ln, font=font_h) <= max_w for ln in lines):
            break
    line_h = size + 6
    y = band_top + (TH - band_top - len(lines) * line_h) / 2
    for ln in lines:
        draw.text((50, y), ln, font=font_h, fill=INK)
        y += line_h

    # Cifra arriba a la izquierda, sobre recuadro oscuro con borde del color.
    if figure:
        font_fig = _font(150, bold=True)
        fw = draw.textlength(figure, font=font_fig)
        fh = font_fig.getbbox("Ag")[3]
        pad = 24
        draw.rectangle([40, 40, 40 + fw + 2 * pad, 40 + fh + 2 * pad], fill=INK, outline=color, width=8)
        draw.text((40 + pad, 40 + pad - 10), figure, font=font_fig, fill=color)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, quality=95)
    return out_path
