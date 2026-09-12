"""Rendimiento relativo, no estimacion causal de demanda.

views / mediana del canal no elimina autoridad, ejecucion, empaque ni sesgo de
seleccion. La cobertura guarda tambien no-outliers para comparar la muestra;
no representa todo YouTube. El analisis visual es un paso separado y auditable.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import median

from .config import DATA_DIR
from .youtube import Channel, Client, Video

MATURITY_DAYS = 7  # antes de esto un video aun no ha acumulado sus views
BASELINE_MIN_VIDEOS = 5  # menos de esto y la mediana no es fiable


@dataclass
class Outlier:
    score: float
    views: int
    title: str
    channel_title: str
    channel_subs: int | None
    channel_baseline: int
    age_days: float
    duration_min: float
    url: str
    engagement: float  # (likes + comentarios) / views, en %
    channel_id: str | None = None
    thumbnail_url: str | None = None


def _baseline(videos: list[Video]) -> int | None:
    """Mediana de views de los videos long-form ya maduros del canal."""
    mature = [v.views for v in videos if not v.is_short and v.age_days >= MATURITY_DAYS]
    if len(mature) < BASELINE_MIN_VIDEOS:
        return None
    value = int(median(mature))
    return value or None


def analyse_channel(
    channel: Channel,
    videos: list[Video],
    *,
    min_score: float,
    max_age_days: float,
    include_shorts: bool,
) -> tuple[list[Outlier], int | None]:
    base = _baseline(videos)
    if base is None:
        return [], None

    found: list[Outlier] = []
    for video in videos:
        if video.is_short and not include_shorts:
            continue
        if not (MATURITY_DAYS <= video.age_days <= max_age_days):
            continue
        score = video.views / base
        if score < min_score:
            continue
        engagement = ((video.likes + video.comments) / video.views * 100) if video.views else 0.0
        found.append(
            Outlier(
                score=round(score, 2),
                views=video.views,
                title=video.title,
                channel_title=channel.title,
                channel_subs=channel.subscribers,
                channel_baseline=base,
                age_days=round(video.age_days, 1),
                duration_min=round(video.duration_s / 60, 1),
                url=video.url,
                engagement=round(engagement, 2),
                channel_id=channel.channel_id,
                thumbnail_url=video.thumbnail_url,
            )
        )
    return found, base


def mine(
    client: Client,
    niche: dict,
    *,
    min_score: float = 3.0,
    max_age_days: float = 180,
    per_channel: int = 60,
    include_shorts: bool = False,
    coverage: dict | None = None,
) -> tuple[list[Outlier], list[str]]:
    """Devuelve (outliers ordenados por score, avisos)."""
    outliers: list[Outlier] = []
    warnings: list[str] = []
    if coverage is not None:
        coverage.update(scope="seed_channel_sample", requested_channels=len(niche["seed_channels"]),
                        per_channel=per_channel, channels=[], videos=[], min_score=min_score,
                        max_age_days=max_age_days, include_shorts=include_shorts)

    for ref in niche["seed_channels"]:
        try:
            channel = client.resolve_channel(ref)
        except Exception as exc:  # la API puede fallar por canal suelto
            warnings.append(f"{ref}: error al resolver ({exc})")
            continue

        if channel is None:
            warnings.append(f"{ref}: no existe o el handle ha cambiado -> corrige niches/*.yaml")
            continue

        try:
            ids = client.recent_video_ids(channel.uploads_playlist, limit=per_channel)
            videos = client.videos(ids)
        except Exception as exc:
            warnings.append(f"{channel.title}: error al descargar videos ({exc})")
            continue

        found, base = analyse_channel(
            channel,
            videos,
            min_score=min_score,
            max_age_days=max_age_days,
            include_shorts=include_shorts,
        )
        if coverage is not None:
            coverage["channels"].append({"channel_id": channel.channel_id,
                "channel_title": channel.title, "channel_subs": channel.subscribers,
                "retrieved_videos": len(videos), "baseline": base})
            for video in videos:
                if (include_shorts or not video.is_short) and MATURITY_DAYS <= video.age_days <= max_age_days:
                    coverage["videos"].append({"url": video.url, "title": video.title,
                        "channel_id": channel.channel_id, "channel_title": channel.title,
                        "channel_subs": channel.subscribers, "age_days": round(video.age_days, 1),
                        "score": round(video.views / base, 2) if base else None})
        if base is None:
            warnings.append(
                f"{channel.title}: menos de {BASELINE_MIN_VIDEOS} videos long-form maduros, "
                "sin mediana fiable -> descartado"
            )
            continue
        outliers.extend(found)

    outliers.sort(key=lambda o: o.score, reverse=True)
    return outliers, warnings


def save(outliers: list[Outlier], niche_name: str, *, coverage: dict | None = None) -> str:
    DATA_DIR.mkdir(exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = DATA_DIR / f"outliers-{niche_name}-{stamp}.json"
    payload = {
        "niche": niche_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(outliers),
        "outliers": [asdict(o) for o in outliers],
        "coverage": coverage,
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)
