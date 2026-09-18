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
    # Centrado vertical: con el bloque pegado arriba, dos tercios de la pantalla
    # quedaban vacios y el texto se leia pequeno en el movil.
    total = sum(_font(r.size, r.bold).getbbox("Ag")[3] + 14 for r in rows)
    top = max(170, 130 + (H - 200 - total) // 2)
    _draw_block(img, rows, left=120, top=top)
    return img


CONTENT = {
    # -- gancho
    # ---- video 2: el agente que vigila
    "watch_everything_dying": lambda: _terminal(
        [
            Line("  Cluster                        Score  Temp   Verdict", DIM, 26),
            Line("  " + "-" * 62, DIM, 26),
            Line("  building agents                 7.0x  new    dying", RED, 28),
            Line("  just dropped / new release      6.4x  new    dying", RED, 28),
            Line("  courses / full guides           5.7x  new    dying", RED, 28),
            Line("  agentic engineering / harness   5.3x  new    dying", RED, 28),
            Line("  comparisons                     4.9x  new    dying", RED, 28),
            Line("  claude code workflows           4.5x  new    dying", RED, 28),
            Line(""),
            Line("  Everything. Every single one.", YELLOW, 34, True),
        ],
        title="first run",
    ),
    "stale_bug": lambda: _terminal(
        [
            Line("  STALE_DAYS = 90", RED, 40, True),
            Line("  --days 180", FG, 36),
            Line(""),
            Line("  Median age in a 180-day window: ~90 days", DIM, 32),
            Line(""),
            Line("  I was asking: older than 90 days?", FG, 32),
            Line("  Of half the data, the answer is yes.", RED, 34, True),
        ],
        title="the bug",
    ),
    "stale_fix": lambda: _terminal(
        [
            Line("  STALE_FRACTION = 0.65", GREEN, 40, True),
            Line(""),
            Line("  stale = median_age > window * 0.65", GREEN, 34),
            Line(""),
            Line("  95 days in a 180-day window   ->  normal", FG, 30),
            Line("  95 days in a 120-day window   ->  stale", YELLOW, 30),
        ],
        title="the fix",
    ),
    "watch_results": lambda: _terminal(
        [
            Line("  Cluster                     Score  Chans  Verdict", DIM, 26),
            Line("  " + "-" * 64, DIM, 26),
            Line("  building agents              7.0x    4!   late to the party", YELLOW, 28, True),
            Line("  just dropped / new release   6.4x    3    watch", FG, 28),
            Line("  courses / full guides        5.7x    2    watch", FG, 28),
            Line("  agentic engineering          5.3x    3    watch", FG, 28),
            Line("  claude code workflows        4.5x    2    watch", FG, 28),
        ],
        title="facelessyt watch",
    ),
    "saturation_trap": lambda: _terminal(
        [
            Line("  building agents", FG, 40, True),
            Line(""),
            Line("  median score      7.0x   <- highest in the niche", GREEN, 32),
            Line("  distinct channels    4   <- already covered", RED, 32, True),
            Line(""),
            Line("  Real demand. And you'd be the fifth.", YELLOW, 34, True),
        ],
        title="the trap",
    ),
    "three_signals": lambda: _terminal(
        [
            Line("  A snapshot can't tell you:", DIM, 32),
            Line(""),
            Line("  temperature   is the score rising or falling?", FG, 32),
            Line("  saturation    how many channels got there first?", FG, 32),
            Line("  freshness     how old are the outliers holding it up?", FG, 32),
            Line(""),
            Line("  All three need memory.", GREEN, 36, True),
        ],
        title="what memory buys",
    ),
    "cluster_regex": lambda: _terminal(
        [
            Line("  DEFAULT_CLUSTERS = {", FG, 30),
            Line("    'agentic / harnesses': r'agentic|harness',", GREEN, 30),
            Line("    'building agents':     r'build.*agent|ai agent',", GREEN, 30),
            Line("    'just dropped':        r'just dropped|is here',", GREEN, 30),
            Line("  }", FG, 30),
            Line(""),
            Line("  Not embeddings. Regex.", YELLOW, 34, True),
            Line("  When it surprises me I can see exactly why.", DIM, 30),
        ],
        title="clusters.py",
    ),
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
    # ---- video 6: el harness de retencion (datos de docs/09, 2026-09-18)
    "studio_180": lambda: _terminal(
        [
            Line("Channel analytics       Last 28 days", DIM, 40),
            Line(""),
            Line("Videos                         5", FG, 50),
            Line("Views                        180", RED, 60, True),
            Line("Watch time (hours)           1.3", FG, 50),
            Line("Subscribers                   +1", FG, 50),
        ],
        title="YouTube Studio",
    ),
    "ctr_funnel": lambda: _terminal(
        [
            Line("  Thumbnail impressions      4,200", FG, 50),
            Line("  Click-through rate          1.0%", RED, 60, True),
            Line("  Average view duration       0:55", RED, 60, True),
            Line(""),
            Line("  Browse features   42%   Suggested   34%", DIM, 38),
            Line("  YouTube was pushing them. Nobody clicked.", YELLOW, 40, True),
        ],
        title="28 days",
    ),
    "gate_refuses": lambda: _terminal(
        [
            Line("  $ facelessyt.video render --script 01-outlier-agent.yaml", DIM, 36),
            Line("  29 error(es) de gancho/ritmo", RED, 44, True),
            Line("  No se renderiza.", RED, 44, True),
            Line(""),
            Line("  $ facelessyt upload --thumbnail ep3.jpg ...", DIM, 36),
            Line("  x imagen: 82% de pixeles casi negros", RED, 40),
            Line("  No se sube.", RED, 44, True),
        ],
        title="the gate",
    ),
    "thresholds_table": lambda: _terminal(
        [
            Line("  Metric                 Threshold   If it fails, the problem is", DIM, 36),
            Line("  " + "-" * 70, DIM, 36),
            Line("  Click-through rate        > 4%      packaging", FG, 40),
            Line("  Retention at 30 s        > 55%      the hook", FG, 40),
            Line("  Average retention        > 40%      script or pacing", FG, 40),
            Line(""),
            Line("  Written on day 0. docs/00-estrategia.md", GREEN, 38),
        ],
        title="the plan",
    ),
    "results_table": lambda: _terminal(
        [
            Line("  Ep  Length   Views   Avg view   Retention", DIM, 36),
            Line("  " + "-" * 50, DIM, 36),
            Line("   1   20:10     101     1:07       5.6%", RED, 40),
            Line("   2   16:14      21     0:25       2.6%", RED, 40),
            Line("   3   11:21      23     1:21      12.0%", RED, 40),
            Line("   4    6:00       8     0:11       3.1%", RED, 40),
            Line("   5    3:51      27     0:52      22.6%", FG, 40),
            Line(""),
            Line("  CTR: 1.0%     none above any threshold", RED, 40, True),
        ],
        title="what happened",
    ),
    "results_table_highlight": lambda: _terminal(
        [
            Line("  Ep  Length   Views   Avg view   Retention   Motion", DIM, 36),
            Line("  " + "-" * 60, DIM, 36),
            Line("   1   20:10     101     1:07       5.6%      stills", DIM, 40),
            Line("   2   16:14      21     0:25       2.6%      stills", DIM, 40),
            Line("   3   11:21      23     1:21      12.0%      stills", DIM, 40),
            Line("   4    6:00       8     0:11       3.1%      stills", DIM, 40),
            Line("   5    3:51      27     0:52      22.6%      canvas", GREEN, 44, True),
            Line(""),
            Line("  4x the retention. The only one that moved.", GREEN, 40, True),
        ],
        title="the signal",
    ),
    "thumb_metrics_cmd": lambda: _terminal(
        [
            Line("  $ facelessyt research            # competitors, 26 outliers", DIM, 36),
            Line("  luminance, saturation, near-black pixels, OCR", FG, 38),
            Line(""),
            Line("  $ facelessyt packaging --thumbnail mine.jpg", GREEN, 46, True),
            Line("  same metrics. my own thumbnails.", FG, 38),
        ],
        title="measure, don't argue",
    ),
    "thumb_metrics_table": lambda: _terminal(
        [
            Line("                       luminance   saturation   near-black", DIM, 36),
            Line("  " + "-" * 62, DIM, 36),
            Line("  26 niche outliers       0.33        0.35         42%", GREEN, 40, True),
            Line("  episode 1               0.10        0.09         86%", RED, 40),
            Line("  episode 2               0.21        0.10         75%", RED, 40),
            Line("  episode 3               0.14        0.26         82%", RED, 40),
            Line("  episode 4               0.12        0.42         80%", RED, 40),
            Line("  episode 5               0.26        0.64         51%", FG, 40),
        ],
        title="thumbnails, measured",
    ),
    "thumb_text_pronouns": lambda: _terminal(
        [
            Line('  "IT LIED"', RED, 56, True),
            Line('  "IT FITS?"', RED, 56, True),
            Line('  "I FOUND IT"', RED, 56, True),
            Line('  "IT\'S A TRAP"', RED, 56, True),
            Line(""),
            Line("  What lied? What fits? Found what?", YELLOW, 40, True),
            Line("  The thumbnail is read before the title.", DIM, 38),
        ],
        title="the text",
    ),
    "bad_hook_quote": lambda: _terminal(
        [
            Line("  hook-1:", DIM, 38),
            Line('  "This channel has zero videos', RED, 48, True),
            Line('   and zero subscribers."', RED, 48, True),
            Line(""),
            Line("  New viewers: 96.6%", FG, 40),
            Line("  A reason to leave, in the first sentence.", YELLOW, 40, True),
        ],
        title="video 1, second 0",
    ),
    "lint_constants": lambda: _terminal(
        [
            Line("  # video/lint.py", DIM, 36),
            Line("  HOOK_FIRST_SCENE_MAX_WORDS = 30", GREEN, 40),
            Line("  HOOK_WINDOW_WORDS          = 95   # ~30 s", GREEN, 40),
            Line("  HOOK_MIN_VISUAL_CHANGES    = 3", GREEN, 40),
            Line("  SCENE_MAX_WORDS            = 55", GREEN, 40),
            Line("  MAX_MINUTES_DEFAULT        = 8", GREEN, 40),
            Line(""),
            Line("  Every rule is a number with a name.", YELLOW, 40, True),
        ],
        title="lint.py",
    ),
    "lint_hook_rules": lambda: _terminal(
        [
            Line("  first scene:  <= 30 words", FG, 40),
            Line("                must contain a digit, 'watch', 'look', or 'you'", FG, 40),
            Line(""),
            Line("  banned in scenes 1-2:", DIM, 38),
            Line('    "this channel"  "subscriber"  "welcome"', RED, 40),
            Line('    "last video"    "in this video"  "my name is"', RED, 40),
        ],
        title="hook rules",
    ),
    "lint_pacing_rules": lambda: _terminal(
        [
            Line("  any scene:     <= 55 words on one image  (~17 s)", FG, 40),
            Line("  first 30 s:    >= 3 different visuals", FG, 40),
            Line("  whole video:   <= 8 min", FG, 40),
            Line(""),
            Line("  until average retention > 40%", YELLOW, 40, True),
        ],
        title="pacing rules",
    ),
    "lint_run_video1": lambda: _terminal(
        [
            Line("  $ facelessyt.video check --script scripts/01-outlier-agent.yaml", DIM, 32),
            Line("  Escenas      : 78", FG, 38),
            Line("  Duracion est.: 21.1 min (maximo 8)", FG, 38),
            Line(""),
            Line("  ERROR hook-self-talk   hook-1   'this channel', 'subscriber'", RED, 36),
            Line("  ERROR hook-payoff      hook-1   nothing concrete in scene 1", RED, 36),
            Line("  ERROR scene-too-long   formula-4b   72 words on one image", RED, 36),
            Line("  ERROR too-long         21.1 min estimated; max 8", RED, 36),
            Line("  ...", DIM, 36),
            Line("  61 aviso(s), 29 error(es)   ->   exit 1", RED, 44, True),
        ],
        title="video 1 vs the linter",
    ),
    "packaging_rules": lambda: _terminal(
        [
            Line("  image:   luminance  >= 0.22", FG, 40),
            Line("           saturation >= 0.20", FG, 40),
            Line("           near-black <= 60%", FG, 40),
            Line(""),
            Line("  text:    <= 4 words", FG, 40),
            Line("           no 'it' / 'this' / 'I' as subject", FG, 40),
            Line("           must not repeat the title", FG, 40),
            Line(""),
            Line("  title:   <= 60 chars, payoff in the first 40", FG, 40),
        ],
        title="packaging.py",
    ),
    "packaging_reject_ep3": lambda: _terminal(
        [
            Line('  $ facelessyt packaging --title "I Built an AI Agent That Has to Prove..."', DIM, 30),
            Line('        --thumb-text "IT LIED" --thumbnail ep3.jpg', DIM, 30),
            Line(""),
            Line("  Miniatura: luminancia 0.14  saturacion 0.26  casi negro 82%", FG, 36),
            Line("  x titulo: 'I Built an AI Agent...' ya se uso dos veces", RED, 36),
            Line("  x texto: empieza por 'it': un pronombre sin referente", RED, 36),
            Line("  x texto: ninguna palabra nombra algo concreto", RED, 36),
            Line("  x imagen: luminancia 0.14 < 0.22", RED, 36),
            Line("  x imagen: 82% de pixeles casi negros; maximo 60%", RED, 36),
            Line("  exit 1", RED, 44, True),
        ],
        title="episode 3 vs the gate",
    ),
    "upload_refuses": lambda: _terminal(
        [
            Line("  $ facelessyt upload --video ep.mp4 --thumbnail dark.jpg ...", DIM, 36),
            Line(""),
            Line("  x imagen: 82% de pixeles casi negros; maximo 60%", RED, 38),
            Line(""),
            Line("  No se sube.", RED, 56, True),
            Line("  Arregla el packaging o usa --skip-packaging-check.", DIM, 38),
        ],
        title="upload",
    ),
    "render_changes": lambda: _terminal(
        [
            Line("  every still     zoompan  1.00 -> 1.08, alternating", GREEN, 40),
            Line("  every cut       xfade    0.25 s", GREEN, 40),
            Line("  music bed       -17 dB under the voice, looped", GREEN, 40),
            Line("  chapters        computed from the real cut", GREEN, 40),
            Line(""),
            Line("  No frame sits still. Nothing else changed.", YELLOW, 40, True),
        ],
        title="assemble.py",
    ),
    "piper_measured": lambda: _terminal(
        [
            Line("  38 words, en_US-lessac-medium, inside the container", DIM, 36),
            Line(""),
            Line("  no flags                     12.9 s   ~176 wpm", FG, 40),
            Line("  length_scale 0.85 + 0.1 s    12.3 s   ~185 wpm", GREEN, 40, True),
            Line("  length_scale 0.80 + 0 s      10.9 s   ~210 wpm", FG, 40),
            Line(""),
            Line("  Measured, not guessed.", YELLOW, 40, True),
        ],
        title="voice.py",
    ),
    "thumb_new_audit": lambda: _terminal(
        [
            Line("  $ facelessyt packaging --thumbnail data/video/06/thumbnail.jpg", DIM, 32),
            Line(""),
            Line("  luminancia 0.37   saturacion 0.57   casi negro 54%", GREEN, 40, True),
            Line("  Packaging OK: pasa los umbrales de los outliers del nicho", GREEN, 38),
            Line(""),
            Line("  Built by code, to pass its own gate.", YELLOW, 40, True),
        ],
        title="this video's thumbnail",
    ),
    "success_criteria": lambda: _terminal(
        [
            Line("  8 videos through the gate. Then:", DIM, 38),
            Line(""),
            Line("  CTR                  1.0%   ->   > 3%", FG, 46),
            Line("  Average retention   5-22%   ->   > 30%", FG, 46),
            Line(""),
            Line("  If those move and views don't: the niche.", YELLOW, 40, True),
            Line("  Not a promise. A test.", DIM, 38),
        ],
        title="how I'll know",
    ),
    "your_turn_packaging": lambda: _terminal(
        [
            Line("  $ git clone github.com/tapaderuza/facelessyt", GREEN, 40),
            Line("  $ facelessyt packaging --thumbnail yours.jpg", GREEN, 40),
            Line(""),
            Line("  Post your near-black number in the comments.", FG, 40, True),
            Line("  Was 86% special, or is everyone doing this?", DIM, 38),
        ],
        title="your turn",
    ),
    "repo_final_06": lambda: _terminal(
        [
            Line(""),
            Line("  github.com/tapaderuza/facelessyt", GREEN, 56, True),
            Line(""),
            Line("  Linter, gate and measurements. MIT.", FG, 40),
            Line("  Video 7 goes through the same gate.", FG, 40),
        ],
        title="Outlier Engineering",
    ),
    # ---- video 7: la llamada de pago dentro del bucle de reintentos (2026-09-18)
    "render_fail_24": lambda: _terminal(
        [
            Line("  [22/24] close-1      14.1s  (44 words)   elevenlabs  $", FG, 36),
            Line("  [23/24] close-2      11.5s  (38 words)   elevenlabs  $", FG, 36),
            Line("  [24/24] close-3       6.6s  (23 words)   elevenlabs  $", FG, 36),
            Line(""),
            Line("  FALLO en el montaje", RED, 50, True),
            Line("  Error muxing a packet: Cannot allocate memory", RED, 36),
        ],
        title="render, scene 24 of 24",
    ),
    "credit_hit": lambda: _terminal(
        [
            Line("  one render          4,177 credits", FG, 44),
            Line("  monthly plan       30,000 credits", FG, 44),
            Line(""),
            Line("  one retry   =   13.9% of the month", RED, 56, True),
            Line(""),
            Line("  for a bug in ffmpeg, not in the voice", YELLOW, 38, True),
        ],
        title="the bill",
    ),
    "twelve_lines_teaser": lambda: _terminal(
        [
            Line("  def once(marker, key, produce):", GREEN, 44, True),
            Line("      ...", DIM, 44),
            Line(""),
            Line("  12 lines.  No database.  No framework.", FG, 40),
            Line("  Pay once. Retry for free.", YELLOW, 44, True),
        ],
        title="paidcache.py",
    ),
    "pipeline_flow": lambda: _terminal(
        [
            Line("  script.yaml", FG, 40),
            Line("      |  24 scenes", DIM, 34),
            Line("      v", DIM, 34),
            Line("  voice        text -> mp3        x24", FG, 40),
            Line("  clip         png + mp3 -> mp4   x24", FG, 40),
            Line("  join         24 mp4 -> 1 mp4    x1", FG, 40),
        ],
        title="the pipeline",
    ),
    "pipeline_flow_paid": lambda: _terminal(
        [
            Line("  voice        text -> mp3        x24    PAID   1 credit / char", RED, 40, True),
            Line("  clip         png + mp3 -> mp4   x24    free   local ffmpeg", DIM, 40),
            Line("  join         24 mp4 -> 1 mp4    x1     free   local ffmpeg", DIM, 40),
            Line(""),
            Line("  the only step that costs money is the first one", YELLOW, 36, True),
        ],
        title="who bills",
    ),
    "oom_log": lambda: _terminal(
        [
            Line("  ffmpeg -i clips/hook-1.mp4 -i clips/hook-2.mp4 ... (24 inputs)", DIM, 30),
            Line("  -filter_complex xfade=...;acrossfade=...", DIM, 30),
            Line(""),
            Line("  [vost#0:0/libx264] Error submitting a packet to the muxer:", RED, 34),
            Line("      Cannot allocate memory", RED, 40, True),
            Line("  [out#0/mp4] Task finished with error code: -12", RED, 34),
            Line(""),
            Line("  docker: freqtrade hyperopt running in the next container", YELLOW, 32),
        ],
        title="the join, verbatim",
    ),
    "credit_math": lambda: _terminal(
        [
            Line("  24 scenes, 739 words", DIM, 34),
            Line("  characters            4,177", FG, 44),
            Line("  credits / character       1", FG, 44),
            Line("  credits / render      4,177", GREEN, 50, True),
            Line(""),
            Line("  plan (Starter)       30,000 / month", FG, 40),
        ],
        title="the math",
    ),
    "budget_table": lambda: _terminal(
        [
            Line("                        credits/video    videos/month", DIM, 34),
            Line("  " + "-" * 56, DIM, 34),
            Line("  no cache, 1 retry         8,354             3", RED, 44, True),
            Line("  cache                     4,177             7", GREEN, 44, True),
            Line(""),
            Line("  same plan. same voice. less than half the output.", YELLOW, 34, True),
        ],
        title="30,000 credits",
    ),
    "build_scene_before": lambda: _terminal(
        [
            Line("  def build_scene(scene, workdir):", FG, 36),
            Line("      png   = scenes.render(scene, ...)", FG, 36),
            Line("      audio = voice.synthesise(narration, ...)   # <-- paid, every run", RED, 36, True),
            Line("      clip  = encode_still(png, audio, ...)", FG, 36),
            Line("      return Clip(...)", FG, 36),
            Line(""),
            Line("  for scene in scenes: build_scene(scene)", DIM, 34),
            Line("  concat(clips)                               # <-- this is what failed", RED, 34),
        ],
        title="assemble.py, before",
    ),
    "retry_unit": lambda: _terminal(
        [
            Line("  retry unit = [ expensive step ] + [ fragile step ]", FG, 40),
            Line(""),
            Line("      expensive:  24 paid API calls", RED, 40),
            Line("      fragile:    one ffmpeg join", YELLOW, 40),
            Line(""),
            Line("  fragile fails  ->  whole unit reruns  ->  expensive pays again", RED, 36, True),
        ],
        title="the real bug",
    ),
    "same_shape": lambda: _terminal(
        [
            Line("  LLM call        ->  JSON parse fails      ->  pay again", FG, 38),
            Line("  image gen       ->  upload times out      ->  pay again", FG, 38),
            Line("  TTS call        ->  ffmpeg join OOM       ->  pay again", RED, 38, True),
            Line(""),
            Line("  same shape, three different bills", YELLOW, 40, True),
        ],
        title="you have seen this",
    ),
    "paidcache_code": lambda: _terminal(
        [
            Line("  def once(marker, key, produce):", GREEN, 32, True),
            Line("      if marker.exists():", FG, 32),
            Line("          record = json.loads(marker.read_text())", FG, 32),
            Line('          if record["key"] == key and Path(record["path"]).exists():', FG, 32),
            Line('              return Path(record["path"])          # paid before: free', GREEN, 32),
            Line("      result = produce()                            # pay once", RED, 32),
            Line('      marker.write_text(json.dumps({"key": key, "path": str(result)}))', FG, 32),
            Line("      return result", FG, 32),
        ],
        title="paidcache.py",
    ),
    "marker_json": lambda: _terminal(
        [
            Line("  audio/hook-1.mp3", FG, 38),
            Line("  audio/hook-1.key.json", GREEN, 38, True),
            Line(""),
            Line("  {", FG, 36),
            Line('    "key":  "elevenlabs|<voice>|multilingual_v2|...|Watch this render...",', FG, 32),
            Line('    "path": "audio/hook-1.mp3"', FG, 32),
            Line("  }", FG, 36),
        ],
        title="one marker per result",
    ),
    "cache_key_bug": lambda: _terminal(
        [
            Line("  v1:   key = narration", RED, 44, True),
            Line(""),
            Line("  change ELEVENLABS_VOICE_ID", FG, 36),
            Line("  re-render", FG, 36),
            Line("  ...same text, same key, cached audio", DIM, 36),
            Line(""),
            Line("  old voice comes back. No error. No bill either.", RED, 38, True),
        ],
        title="it worked, and it was wrong",
    ),
    "fingerprint_code": lambda: _terminal(
        [
            Line("  def fingerprint(engine):", GREEN, 34, True),
            Line('      return f"elevenlabs|{VOICE_ID}|{MODEL}|{stability}|{similarity}"', FG, 32),
            Line(""),
            Line('  key = fingerprint(engine) + "|" + narration', GREEN, 40, True),
            Line(""),
            Line("  everything that changes the output goes in the key", YELLOW, 36, True),
        ],
        title="voice.py",
    ),
    "rerun_zero_credits": lambda: _terminal(
        [
            Line("  $ render --script 06-retention-harness.yaml", DIM, 32),
            Line(""),
            Line("  scenes reused          24 / 24", GREEN, 50, True),
            Line("  ElevenLabs calls             0", GREEN, 50, True),
            Line("  credits spent                0", GREEN, 50, True),
        ],
        title="second run",
    ),
    "rule_card": lambda: _terminal(
        [
            Line(""),
            Line("  A paid call inside a retry loop", FG, 46, True),
            Line("  needs a cache whose key contains", FG, 46, True),
            Line("  everything that changes its output.", GREEN, 46, True),
            Line(""),
            Line("  Not just the prompt.", YELLOW, 40, True),
        ],
        title="the rule",
    ),
    "where_else": lambda: _terminal(
        [
            Line("  voice        TTS API          key = voice + model + speed + text", FG, 34),
            Line("  thumbnail    image generator  key = model + size + prompt", FG, 34),
            Line("  script       LLM              key = model + temperature + prompt", FG, 34),
            Line(""),
            Line("  same 12 lines. three call sites.", YELLOW, 40, True),
        ],
        title="in this pipeline",
    ),
    "xfade_batch": lambda: _terminal(
        [
            Line("  XFADE_BATCH = 8", GREEN, 44, True),
            Line("  24 clips  ->  3 partial joins  ->  1 final join", FG, 38),
            Line(""),
            Line("  fixes the fragile step", FG, 36),
            Line("  does not protect you from the next fragile step", YELLOW, 36, True),
        ],
        title="assemble.py",
    ),
    "tests_paidcache": lambda: _terminal(
        [
            Line("  OK   same key            -> produce called once", GREEN, 36),
            Line("  OK   different voice     -> produce called again", GREEN, 36),
            Line("  OK   file deleted        -> regenerated", GREEN, 36),
            Line("  OK   fingerprint changes with the voice", GREEN, 36),
            Line(""),
            Line("  Ran 92 tests    OK", GREEN, 44, True),
        ],
        title="tests",
    ),
    "your_turn_paid": lambda: _terminal(
        [
            Line("  1.  find the paid call", FG, 40),
            Line("  2.  find the step after it that can fail", FG, 40),
            Line("  3.  do they share a retry?", YELLOW, 40, True),
            Line(""),
            Line("  github.com/tapaderuza/facelessyt  ->  paidcache.py", GREEN, 36),
        ],
        title="your pipeline",
    ),
    "repo_final_07": lambda: _terminal(
        [
            Line(""),
            Line("  github.com/tapaderuza/facelessyt", GREEN, 56, True),
            Line(""),
            Line("  paidcache.py  -  12 lines, MIT", FG, 40),
            Line("  the voice: ElevenLabs, link below", FG, 40),
        ],
        title="Outlier Engineering",
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
