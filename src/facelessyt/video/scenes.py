"""Renderizado de escenas a imagenes.

Cada escena del guion se convierte en un PNG de 1920x1080. No se graba una
pantalla: se dibuja. Asi el resultado es identico en cada ejecucion, se puede
regenerar el video entero tras cambiar una frase, y no hay que rodar nada.

El contenido visual (`visual.content`) es una clave que se resuelve contra
`CONTENT`, definido mas abajo. Añadir una escena nueva es añadir una entrada ahi.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080

# Paleta: terminal oscura, alto contraste. Verde para lo que importa.
BG = (13, 17, 23)
FG = (201, 209, 217)
DIM = (110, 118, 129)
GREEN = (63, 185, 80)
YELLOW = (210, 153, 34)
RED = (248, 81, 73)
BLUE = (88, 166, 255)

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/consolab.ttf",
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    idx = 1 if bold else 0
    for path in (FONT_CANDIDATES[idx::2] + FONT_CANDIDATES):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


@dataclass
class Line:
    """Una linea de texto con color y escala propios."""

    text: str
    color: tuple[int, int, int] = FG
    size: int = 34
    bold: bool = False


def _draw_lines(img: Image.Image, lines: list[Line], *, top: int | None = None) -> None:
    draw = ImageDraw.Draw(img)
    rendered = [(ln, _font(ln.size, ln.bold)) for ln in lines]
    total = sum(f.getbbox("Ag")[3] + 16 for _, f in rendered)
    y = top if top is not None else (H - total) // 2

    for line, font in rendered:
        width = draw.textlength(line.text, font=font)
        draw.text(((W - width) / 2, y), line.text, font=font, fill=line.color)
        y += font.getbbox("Ag")[3] + 16


def _draw_block(img: Image.Image, lines: list[Line], *, left: int = 140, top: int = 160) -> None:
    """Texto alineado a la izquierda: para terminal y codigo."""
    draw = ImageDraw.Draw(img)
    y = top
    for line in lines:
        font = _font(line.size, line.bold)
        draw.text((left, y), line.text, font=font, fill=line.color)
        y += font.getbbox("Ag")[3] + 14


def _canvas() -> Image.Image:
    return Image.new("RGB", (W, H), BG)


# --------------------------------------------------------------------------
# Contenido de cada escena. La clave coincide con `visual.content` del guion.
# --------------------------------------------------------------------------


def _huge_number(text: str) -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    font = _font(340, bold=True)
    width = draw.textlength(text, font=font)
    draw.text(((W - width) / 2, H / 2 - 210), text, font=font, fill=GREEN)
    return img


def _centered_text(text: str, size: int = 78, color=FG) -> Image.Image:
    img = _canvas()
    # Parte frases largas en varias lineas para que quepan.
    words, lines, current = text.split(), [], ""
    for word in words:
        probe = f"{current} {word}".strip()
        if len(probe) > 34 and current:
            lines.append(current)
            current = word
        else:
            current = probe
    lines.append(current)
    _draw_lines(img, [Line(ln, color, size, bold=True) for ln in lines])
    return img


def _terminal(rows: list[Line], title: str = "facelessyt") -> Image.Image:
    img = _canvas()
    draw = ImageDraw.Draw(img)
    # Barra de ventana
    draw.rectangle([80, 70, W - 80, 130], fill=(22, 27, 34))
    for i, color in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        draw.ellipse([110 + i * 34, 92, 128 + i * 34, 110], fill=color)
    draw.text((240, 88), title, font=_font(28), fill=DIM)
    draw.rectangle([80, 130, W - 80, H - 70], fill=(13, 17, 23), outline=(48, 54, 61))
    _draw_block(img, rows, left=120, top=170)
    return img


CONTENT = {
    # -- gancho
    "empty_studio": lambda: _terminal(
        [
            Line("Channel analytics", DIM, 32),
            Line(""),
            Line("Subscribers          0", FG, 38),
            Line("Videos               0", FG, 38),
            Line("Views                0", FG, 38),
            Line("Watch time (hours)   0", FG, 38),
        ],
        title="YouTube Studio",
    ),
    "12.7x": lambda: _huge_number("12.7x"),
    "outlier_row_highlight": lambda: _terminal(
        [
            Line("  Score     Views   Title                                  Channel            Subs", DIM, 26),
            Line("  " + "-" * 92, DIM, 26),
            Line("  12.7x    182.3k   Anthropic Just Dropped the New...      The AI Automators  64.4k", GREEN, 28, True),
            Line("  10.5x    158.7k   Google Just Dropped a Masterclass...   Cole Medin          225k", FG, 28),
            Line("   7.7x    779.8k   How AI agents & Claude skills work     Greg Isenberg       707k", FG, 28),
            Line("   7.6x    399.1k   Matt Pocock's Agentic Workflow...      David Ondrej        415k", FG, 28),
        ]
    ),
    # -- problema
    "The second decision": lambda: _centered_text("Editing is the second decision"),
    "Does this topic have demand?": lambda: _centered_text("Does this topic have demand?"),
    "search_vs_recommendation": lambda: _canvas_split(
        ("SEARCH ENGINE", "keyword volume", RED),
        ("RECOMMENDATION ENGINE", "what YouTube pushes", GREEN),
    ),
    "It's free. It's public. Nobody uses it.": lambda: _centered_text(
        "Free. Public. Almost nobody uses it."
    ),
    # -- las views mienten
    "two_videos": lambda: _canvas_split(
        ("400,000 views", "", FG), ("97,000 views", "", FG)
    ),
    "two_videos_annotated_big": lambda: _canvas_split(
        ("400,000 views", "channel averages 1M  ->  UNDERPERFORMED", RED),
        ("97,000 views", "", DIM),
    ),
    "two_videos_annotated_small": lambda: _canvas_split(
        ("400,000 views", "0.4x", DIM),
        ("97,000 views", "64k subs  ->  6.8x its own median", GREEN),
    ),
    "Views measure the channel. Not the topic.": lambda: _centered_text(
        "View count measures the channel. I want the topic.", size=64
    ),
    # -- formula
    "formula": lambda: _terminal(
        [
            Line(""),
            Line("  outlier_score = views / channel median views", GREEN, 46, True),
        ],
        title="the whole idea",
    ),
    "formula_annotated": lambda: _terminal(
        [
            Line("  outlier_score = views / channel median views", GREEN, 42, True),
            Line(""),
            Line("  1.0x   normal for that channel", DIM, 32),
            Line("  3.0x   tripled its own baseline", FG, 32),
            Line("  12.7x  the algorithm picked it up", GREEN, 32),
            Line(""),
            Line("  channel size cancels out", BLUE, 34, True),
        ],
        title="the whole idea",
    ),
    "median_vs_mean": lambda: _terminal(
        [
            Line("  views = [1000, 1000, 1000, 1000, 900000]", FG, 34),
            Line(""),
            Line("  mean   = 180,800   <- one viral video ruins it", RED, 34),
            Line("  median =   1,000   <- unbothered", GREEN, 34),
        ],
        title="median, not average",
    ),
    "maturity_filter": lambda: _terminal(
        [
            Line("  MATURITY_DAYS = 7", GREEN, 38, True),
            Line(""),
            Line("  A 3-day-old video hasn't earned its views yet.", DIM, 32),
            Line("  Score it and every new upload looks like a failure.", DIM, 32),
        ],
        title="miner.py",
    ),
    # -- build
    "quota_table": lambda: _terminal(
        [
            Line("  QUOTA_COST = {", FG, 34),
            Line('      "channels":       1,', FG, 34),
            Line('      "playlistItems":  1,', FG, 34),
            Line('      "videos":         1,', FG, 34),
            Line('      "search":       100,   # <-- ouch', RED, 34),
            Line("  }", FG, 34),
            Line(""),
            Line("  Daily free quota: 10,000 units", DIM, 32),
        ],
        title="youtube.py",
    ),
    "quota_strategy": lambda: _terminal(
        [
            Line("  seed channel  ->  uploads playlist  ->  videos", FG, 34),
            Line("       1 unit          1 per 50           1 per 50", DIM, 30),
            Line(""),
            Line("  Full run: 12 channels, 720 videos", FG, 34),
            Line("  Cost: 60 units of 10,000", GREEN, 40, True),
        ],
        title="youtube.py",
    ),
    "tests_passing": lambda: _terminal(
        [
            Line("  OK    test_outlier_detectado", GREEN, 30),
            Line("  OK    test_videos_inmaduros_se_ignoran", GREEN, 30),
            Line("  OK    test_shorts_excluidos_del_baseline", GREEN, 30, True),
            Line("  OK    test_canal_con_pocos_videos_se_descarta", GREEN, 30),
            Line("  OK    test_corte_pasa_con_3_hits_y_tendencia", GREEN, 30),
            Line("  OK    test_corte_falla_si_plano", GREEN, 30),
            Line(""),
            Line("  11/11 tests pasan", GREEN, 36, True),
        ],
        title="tests",
    ),
    "analyse_channel": lambda: _terminal(
        [
            Line("  base = median(mature long-form views)", FG, 32),
            Line(""),
            Line("  for video in videos:", FG, 32),
            Line("      if video.is_short: continue", FG, 32),
            Line("      if video.age_days < 7: continue", FG, 32),
            Line("      score = video.views / base", GREEN, 32, True),
            Line("      if score >= min_score:", FG, 32),
            Line("          found.append(video)", FG, 32),
        ],
        title="miner.py",
    ),
    "worked_example": lambda: _terminal(
        [
            Line("  The AI Automators - last 60 uploads", DIM, 30),
            Line(""),
            Line("  long-form, older than 7 days:  41 videos", FG, 32),
            Line("  median views:                  14,300", GREEN, 34, True),
            Line(""),
            Line("  that one video:               182,300", FG, 34),
            Line("  182,300 / 14,300           =    12.7x", GREEN, 40, True),
        ],
        title="doing it by hand",
    ),
    "what_id_change": lambda: _terminal(
        [
            Line("  What I'd change next:", YELLOW, 38, True),
            Line(""),
            Line("  - weight recent outliers higher", FG, 32),
            Line("  - track clusters across runs", FG, 32),
            Line("  - flag topics already saturated", FG, 32),
            Line("  - pull CTR once I own the channel", FG, 32),
        ],
        title="not done yet",
    ),
    "Nothing under 3x gets made": lambda: _centered_text(
        "Nothing under 3x gets made", size=72
    ),
    # -- fallo en verde
    "check_green_marclou": lambda: _terminal(
        [
            Line("  Reference        Status   Channel        Subs   Videos", DIM, 30),
            Line("  " + "-" * 66, DIM, 30),
            Line("  @nicksaraev      OK       Nick Saraev    516k      325", FG, 30),
            Line("  @LiamOttley      OK       Liam Ottley    848k      255", FG, 30),
            Line("  @MarcLou         OK       miilinks          6        0", GREEN, 32, True),
        ],
        title="facelessyt check",
    ),
    "check_green_marclou_zoom": lambda: _terminal(
        [
            Line(""),
            Line("  @MarcLou    OK    miilinks    6 subs    0 videos", GREEN, 42, True),
            Line(""),
            Line("  Handle abandoned. Someone else claimed it.", RED, 38),
            Line("  It passed. In green.", RED, 38, True),
        ],
        title="facelessyt check",
    ),
    "min_seed_videos_fix": lambda: _terminal(
        [
            Line("  MIN_SEED_VIDEOS = 20", GREEN, 40, True),
            Line(""),
            Line("  @MarcLou    SUSPICIOUS    miilinks    6    0", RED, 34),
            Line(""),
            Line("  A red error costs 30 seconds.", DIM, 32),
            Line("  A silent green pass costs weeks.", YELLOW, 34, True),
        ],
        title="cli.py",
    ),
    # -- ejecucion
    "mine_command": lambda: _terminal(
        [Line("  $ facelessyt mine --min-score 3", GREEN, 44, True)],
        title="terminal",
    ),
    "mine_results_full": lambda: _terminal(
        [
            Line("  Score     Views   Title                                    Channel             Subs", DIM, 24),
            Line("  " + "-" * 96, DIM, 24),
            Line("  12.7x    182.3k   Anthropic Just Dropped the Blueprint...  The AI Automators   64.4k", GREEN, 26, True),
            Line("  10.5x    158.7k   Google Just Dropped a Masterclass...     Cole Medin           225k", FG, 26),
            Line("   7.7x    779.8k   How AI agents & Claude skills work       Greg Isenberg        707k", FG, 26),
            Line("   7.6x    399.1k   Matt Pocock's Agentic Workflow...        David Ondrej         415k", FG, 26),
            Line("   7.3x    300.1k   How to Build & Sell AI Agents in 2026    Liam Ottley          848k", FG, 26),
            Line("   7.1x    107.8k   Full Archon Guide - Build AI Coding...   Cole Medin           225k", FG, 26),
            Line("   6.8x     97.6k   Karpathy's Math Proves Agent Skills...   The AI Automators   64.4k", FG, 26),
            Line("   6.6x    436.7k   CLAUDE CODE ADVANCED FULL COURSE         Nick Saraev          516k", FG, 26),
            Line("   6.3x     96.3k   Finally, an Open Standard for the...     Cole Medin           225k", FG, 26),
            Line("   5.5x     82.8k   Harness Engineering: What Separates...   Cole Medin           225k", FG, 26),
            Line(""),
            Line("  26 topics with proven demand      Quota used: 60 / 10000", GREEN, 30, True),
        ],
        title="facelessyt mine",
    ),
    "mine_results_top": lambda: _terminal(
        [
            Line(""),
            Line("  12.7x", GREEN, 90, True),
            Line(""),
            Line("  The AI Automators   64,400 subscribers", FG, 38),
            Line("  182,300 views on one video", FG, 38),
            Line("  Channel median: 14,300", DIM, 34),
        ],
        title="the cleanest signal",
    ),
    # -- hallazgos
    "Three things I didn't expect": lambda: _centered_text("Three things I didn't expect"),
    "findings_table_size": lambda: _terminal(
        [
            Line("  Channel size        Outliers    Avg score", DIM, 34),
            Line("  " + "-" * 46, DIM, 34),
            Line("  <= 250k subs             13         6.0x", GREEN, 38, True),
            Line("   > 250k subs             13         5.1x", FG, 38),
            Line(""),
            Line("  Small channels are where topics prove themselves.", BLUE, 32),
        ],
        title="finding 1",
    ),
    "findings_table_duration": lambda: _terminal(
        [
            Line("  What I assumed:   8-15 minutes", RED, 40),
            Line("  What the data says:", DIM, 34),
            Line(""),
            Line("  Median outlier duration     28 min", GREEN, 44, True),
            Line("  Median of the top 10        29 min", GREEN, 44, True),
        ],
        title="finding 2",
    ),
    "findings_table_clusters": lambda: _terminal(
        [
            Line("  Cluster                        Outliers   Avg score", DIM, 32),
            Line("  " + "-" * 54, DIM, 32),
            Line("  Building agents                     5        7.2x", GREEN, 34, True),
            Line("  New model / tool just dropped       7        6.5x", FG, 34),
            Line("  Agentic engineering / harnesses     8        6.0x", GREEN, 34, True),
            Line("  Claude Code workflows               6        5.0x", FG, 34),
            Line(""),
            Line("  8 hits. 5 independent channels.", BLUE, 34, True),
        ],
        title="finding 3",
    ),
    "What the data does NOT say": lambda: _terminal(
        [
            Line("  What this does NOT tell you:", YELLOW, 40, True),
            Line(""),
            Line("  x  Click-through rate", RED, 36),
            Line("  x  Retention", RED, 36),
            Line(""),
            Line("  The public API exposes neither.", DIM, 32),
            Line("  I know what pulls clicks.", FG, 34),
            Line("  I don't know yet what holds them.", FG, 34),
        ],
        title="be honest",
    ),
    # -- bug de docker
    "docker_error": lambda: _terminal(
        [
            Line("  $ docker compose run --rm facelessyt check", DIM, 30),
            Line(""),
            Line("  OK  API key loaded", GREEN, 32),
            Line("  Config error: niche 'ai-automation' not found", RED, 32, True),
            Line("  (/usr/local/lib/python3.12/niches/ai-automation.yaml)", RED, 28),
            Line(""),
            Line("  Available: (none)", RED, 30),
        ],
        title="it broke immediately",
    ),
    "root_detection_bug": lambda: _terminal(
        [
            Line("  ROOT = Path(__file__).resolve().parents[2]", RED, 36, True),
            Line(""),
            Line("  cloned repo:", DIM, 30),
            Line("    src/facelessyt/config.py  ->  project root   OK", GREEN, 30),
            Line(""),
            Line("  installed in a container:", DIM, 30),
            Line("    site-packages/facelessyt/  ->  /usr/local/lib   WRONG", RED, 30, True),
        ],
        title="the bug",
    ),
    "root_detection_fix": lambda: _terminal(
        [
            Line("  def _detect_root():", FG, 32),
            Line("      if os.getenv('FACELESSYT_ROOT'): ...", GREEN, 32),
            Line("      if (repo_root / 'niches').is_dir(): ...", GREEN, 32),
            Line("      return Path.cwd()", GREEN, 32),
            Line(""),
            Line("  That bug was there the whole time.", YELLOW, 36, True),
            Line("  Containerizing was a test I didn't know", DIM, 32),
            Line("  I was running.", DIM, 32),
        ],
        title="the fix",
    ),
    # -- cierre
    "docker_commands": lambda: _terminal(
        [
            Line("  $ git clone github.com/tapaderuza/facelessyt", GREEN, 34),
            Line("  $ docker compose run --rm facelessyt mine", GREEN, 34),
            Line(""),
            Line("  Free. MIT. Any niche you want.", FG, 36, True),
        ],
        title="your turn",
    ),
    "What's your highest score?": lambda: _centered_text(
        "What's the highest score you get?", size=68
    ),
    "repo_final": lambda: _terminal(
        [
            Line(""),
            Line("  github.com/tapaderuza/facelessyt", GREEN, 46, True),
            Line(""),
            Line("  Next: I build the top topic on this list", FG, 36),
            Line("  and we find out if the tool was right.", FG, 36),
        ],
        title="Outlier Engineering",
    ),
}


def _canvas_split(left: tuple, right: tuple) -> Image.Image:
    """Dos columnas comparadas. Cada tupla es (titulo, subtitulo, color)."""
    img = _canvas()
    draw = ImageDraw.Draw(img)
    draw.line([(W // 2, 220), (W // 2, H - 220)], fill=(48, 54, 61), width=3)

    for (title, sub, color), cx in ((left, W // 4), (right, 3 * W // 4)):
        font = _font(60, bold=True)
        draw.text((cx - draw.textlength(title, font=font) / 2, H / 2 - 90), title,
                  font=font, fill=color)
        if sub:
            fs = _font(30)
            # Parte el subtitulo si no cabe en la columna.
            words, lines, cur = sub.split(), [], ""
            for word in words:
                probe = f"{cur} {word}".strip()
                if draw.textlength(probe, font=fs) > W / 2 - 120 and cur:
                    lines.append(cur)
                    cur = word
                else:
                    cur = probe
            lines.append(cur)
            for i, line in enumerate(lines):
                draw.text((cx - draw.textlength(line, font=fs) / 2, H / 2 + 20 + i * 42),
                          line, font=fs, fill=DIM)
    return img


class SceneError(RuntimeError):
    pass


def render(scene: dict, out_path: Path) -> Path:
    """Renderiza una escena del guion a PNG."""
    visual = scene.get("visual", {})
    key = visual.get("content", "")

    if key in CONTENT:
        img = CONTENT[key]()
    elif visual.get("type") == "text":
        img = _centered_text(key)
    else:
        raise SceneError(
            f"Escena '{scene.get('id')}': no se sabe dibujar '{key}'. "
            f"Añadelo a CONTENT en scenes.py o usa visual.type=text."
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return out_path
