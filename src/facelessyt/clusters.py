"""Seguimiento de temas entre ejecuciones.

El miner del video 1 responde a "que tira ahora mismo". Eso es una foto, y una
foto no distingue un tema que esta despegando de uno que lleva seis meses
caliente y se esta apagando. Para eso hace falta memoria.

Este modulo agrupa los outliers en clusters, guarda el estado de cada ejecucion
y compara contra las anteriores. Tres senales que la foto no da:

  temperatura : el score medio del cluster sube o baja entre ejecuciones
  saturacion  : cuantos canales distintos ya han cubierto el tema
  frescura    : que edad tienen los outliers que lo sostienen

Un cluster con score alto y saturacion alta es una trampa: hay demanda, pero
llegas el vigesimo. El miner solo, sin esto, te manda directo ahi.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from statistics import median

from .config import DATA_DIR

# Un cluster se define por los patrones que aparecen en el titulo. Es
# deliberadamente simple: un modelo de embeddings seria mas fino y mucho mas
# dificil de auditar cuando el resultado sorprenda.
DEFAULT_CLUSTERS: dict[str, str] = {
    "agentic engineering / harnesses": r"agentic|harness",
    "building agents": r"build.*agent|ai agent|agent skills",
    "just dropped / new release": r"just dropped|just released|is here|new model",
    "claude code workflows": r"claude code|claude routines|claude skills",
    "local models / self-hosting": r"local|self.host|ollama|mlx|gguf",
    "coding tools": r"cursor|copilot|windsurf|cline|coding agent",
    "comparisons": r"\bvs\.?\b|which should|compared",
    "courses / full guides": r"full course|ultimate guide|complete guide|masterclass",
}

# Por encima de esto, el tema ya lo ha cubierto medio nicho.
SATURATION_CHANNELS = 4
# Un cluster esta "viejo" si sus outliers son mayores de lo que cabria esperar
# dentro de la ventana minada. Con una ventana de 180 dias, la edad mediana
# esperada es ~90: un umbral absoluto de 90 marcaria como agotado practicamente
# todo, que es justo lo que hizo la primera version.
STALE_FRACTION = 0.65


@dataclass
class ClusterState:
    name: str
    outliers: int
    median_score: float
    max_score: float
    channels: list[str] = field(default_factory=list)
    median_age_days: float = 0.0
    window_days: float = 180.0

    @property
    def saturated(self) -> bool:
        return len(self.channels) >= SATURATION_CHANNELS

    @property
    def stale(self) -> bool:
        """Viejo RELATIVO a la ventana minada, no en dias absolutos."""
        return self.median_age_days > self.window_days * STALE_FRACTION


@dataclass
class ClusterTrend:
    name: str
    now: ClusterState
    before: ClusterState | None

    @property
    def score_delta(self) -> float | None:
        if self.before is None:
            return None
        return round(self.now.median_score - self.before.median_score, 2)

    @property
    def outlier_delta(self) -> int | None:
        if self.before is None:
            return None
        return self.now.outliers - self.before.outliers

    @property
    def temperature(self) -> str:
        """Que le esta pasando al tema, en una palabra."""
        if self.before is None:
            return "nuevo"
        delta = self.score_delta or 0
        if delta > 0.5 and (self.outlier_delta or 0) >= 0:
            return "calentando"
        if delta < -0.5 or (self.outlier_delta or 0) < 0:
            return "enfriando"
        return "estable"

    @property
    def verdict(self) -> str:
        """Que hacer con el, que es lo que de verdad se pregunta uno."""
        if self.now.saturated and self.temperature == "enfriando":
            return "evitar: saturado y perdiendo fuerza"
        if self.now.saturated:
            return "cuidado: hay demanda pero llegas tarde"
        if self.now.stale:
            return "apagandose: lo sostienen outliers viejos"
        if self.temperature == "calentando":
            return "entrar ahora"
        if self.temperature == "nuevo" and self.now.median_score >= 4:
            return "prometedor: sin historico todavia"
        return "vigilar"


def assign(title: str, patterns: dict[str, str] | None = None) -> list[str]:
    """Clusters a los que pertenece un titulo. Puede ser mas de uno, o ninguno."""
    patterns = patterns or DEFAULT_CLUSTERS
    return [name for name, pat in patterns.items() if re.search(pat, title, re.I)]


def summarise(outliers: list[dict], patterns: dict[str, str] | None = None,
              *, window_days: float = 180.0) -> list[ClusterState]:
    """Agrupa una tanda de outliers en el estado actual de cada cluster."""
    patterns = patterns or DEFAULT_CLUSTERS
    buckets: dict[str, list[dict]] = {}
    for o in outliers:
        for name in assign(o["title"], patterns):
            buckets.setdefault(name, []).append(o)

    states = []
    for name, items in buckets.items():
        scores = [i["score"] for i in items]
        states.append(
            ClusterState(
                name=name,
                outliers=len(items),
                median_score=round(median(scores), 2),
                max_score=round(max(scores), 2),
                channels=sorted({i["channel_title"] for i in items}),
                median_age_days=round(median([i["age_days"] for i in items]), 1),
                window_days=window_days,
            )
        )
    states.sort(key=lambda s: s.median_score, reverse=True)
    return states


# -- persistencia ---------------------------------------------------------

def _history_path(niche: str) -> Path:
    return DATA_DIR / f"clusters-{niche}.jsonl"


def record(states: list[ClusterState], niche: str) -> Path:
    """Guarda el estado de esta ejecucion. Una linea por tanda."""
    DATA_DIR.mkdir(exist_ok=True)
    path = _history_path(niche)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "at": datetime.now(timezone.utc).isoformat(),
            "clusters": [asdict(s) for s in states],
        }, ensure_ascii=False) + "\n")
    return path


def previous(niche: str, *, skip_last: bool = False) -> dict[str, ClusterState]:
    """Estado de la ejecucion anterior, por nombre de cluster."""
    path = _history_path(niche)
    if not path.exists():
        return {}
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if skip_last:
        lines = lines[:-1]
    if not lines:
        return {}
    data = json.loads(lines[-1])
    return {c["name"]: ClusterState(**c) for c in data["clusters"]}


def compare(states: list[ClusterState], niche: str) -> list[ClusterTrend]:
    """Cruza el estado actual con el de la ejecucion anterior."""
    # skip_last porque record() ya ha escrito la tanda actual.
    before = previous(niche, skip_last=True)
    trends = [ClusterTrend(name=s.name, now=s, before=before.get(s.name)) for s in states]

    orden = {"entrar ahora": 0, "prometedor: sin historico todavia": 1, "vigilar": 2,
             "cuidado: hay demanda pero llegas tarde": 3,
             "apagandose: lo sostienen outliers viejos": 4,
             "evitar: saturado y perdiendo fuerza": 5}
    trends.sort(key=lambda t: (orden.get(t.verdict, 9), -t.now.median_score))
    return trends
