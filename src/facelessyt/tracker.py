"""Tracker de la metrica de corte de los 90 dias.

PASA si:  >=3 videos superan 10.000 views  Y  la mediana del ultimo tercio
          de videos es mayor que la del primer tercio.

Cada ejecucion deja una linea en data/history.jsonl, para poder ver la
evolucion y no solo la foto final.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median

from .config import DATA_DIR
from .youtube import Client, Video

HIT_THRESHOLD = 10_000  # views que definen un "hit"
HITS_REQUIRED = 3
TEST_DAYS = 90
TARGET_VIDEOS = 24


@dataclass
class Verdict:
    videos_published: int
    days_elapsed: float
    hits: int
    best_views: int
    median_first_third: float
    median_last_third: float
    trend_up: bool
    passes: bool
    on_pace: bool
    top: list[tuple[str, int]]


def evaluate(videos: list[Video], *, since: datetime | None = None) -> Verdict:
    longform = [v for v in videos if not v.is_short]
    if since:
        longform = [v for v in longform if v.published >= since]
    longform.sort(key=lambda v: v.published)  # cronologico

    if not longform:
        return Verdict(0, 0.0, 0, 0, 0.0, 0.0, False, False, False, [])

    views = [v.views for v in longform]
    third = max(1, len(longform) // 3)
    first_third = median(views[:third])
    last_third = median(views[-third:])
    trend_up = last_third > first_third

    hits = sum(1 for v in views if v >= HIT_THRESHOLD)
    days = (datetime.now(timezone.utc) - longform[0].published).total_seconds() / 86400

    # Ritmo: 24 videos en 90 dias
    expected = min(TARGET_VIDEOS, (days / TEST_DAYS) * TARGET_VIDEOS)
    on_pace = len(longform) >= expected * 0.9

    top = sorted(((v.title, v.views) for v in longform), key=lambda t: t[1], reverse=True)[:5]

    return Verdict(
        videos_published=len(longform),
        days_elapsed=round(days, 1),
        hits=hits,
        best_views=max(views),
        median_first_third=first_third,
        median_last_third=last_third,
        trend_up=trend_up,
        passes=hits >= HITS_REQUIRED and trend_up,
        on_pace=on_pace,
        top=top,
    )


def snapshot(client: Client, channel_id: str) -> tuple[Verdict, str]:
    channel = client.resolve_channel(channel_id)
    if channel is None:
        raise RuntimeError(f"No se encuentra el canal {channel_id}")

    ids = client.recent_video_ids(channel.uploads_playlist, limit=200)
    videos = client.videos(ids)
    verdict = evaluate(videos)

    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / "history.jsonl"
    line = {
        "at": datetime.now(timezone.utc).isoformat(),
        "channel": channel.title,
        "subscribers": channel.subscribers,
        "videos": verdict.videos_published,
        "days": verdict.days_elapsed,
        "hits": verdict.hits,
        "best_views": verdict.best_views,
        "median_first_third": verdict.median_first_third,
        "median_last_third": verdict.median_last_third,
        "passes": verdict.passes,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, ensure_ascii=False) + "\n")

    return verdict, channel.title
