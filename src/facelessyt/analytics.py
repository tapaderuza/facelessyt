"""CTR y retencion: el diagnostico que la Data API no puede dar.

La Data API publica dice cuantas views tiene un video. No dice cuanta gente vio
la miniatura y no hizo clic, ni en que segundo se fueron los que si lo hicieron.
Eso solo lo sabe el dueno del canal, via YouTube Analytics API.

Los umbrales de aqui vienen de docs/00-estrategia.md, y sirven para responder a
una pregunta muy concreta cuando un video no funciona: ¿es el packaging, es el
gancho, o es el nicho?
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from googleapiclient.errors import HttpError

from . import auth

# Umbrales de diagnostico. Ver docs/00-estrategia.md, tabla de la seccion 90 dias.
CTR_MIN = 4.0             # % de impresiones que acaban en clic
RETENTION_30S_MIN = 55.0  # % que sigue ahi a los 30 segundos
RETENTION_AVG_MIN = 40.0  # % de duracion media vista


@dataclass
class VideoDiagnosis:
    video_id: str
    title: str
    views: int
    impressions: int | None
    ctr: float | None                # %
    avg_view_percentage: float | None  # %
    avg_view_duration_s: int | None
    subscribers_gained: int | None
    retention_30s: float | None      # %

    @property
    def verdict(self) -> str:
        """Que esta fallando, en el orden en que se debe mirar."""
        if self.ctr is not None and self.ctr < CTR_MIN:
            return "packaging: el titulo y la miniatura no consiguen el clic"
        if self.retention_30s is not None and self.retention_30s < RETENTION_30S_MIN:
            return "gancho: entran y se van en los primeros 30 segundos"
        if self.avg_view_percentage is not None and self.avg_view_percentage < RETENTION_AVG_MIN:
            return "guion o ritmo: aguantan el principio pero no el cuerpo"
        if all(v is None for v in (self.ctr, self.retention_30s, self.avg_view_percentage)):
            return "sin datos suficientes todavia"
        return "las tres metricas estan bien"


def _query(client, *, ids: str, start: str, end: str, **kwargs) -> dict:
    return client.reports().query(ids=ids, startDate=start, endDate=end, **kwargs).execute()


def retention_at(client, video_id: str, seconds: float, duration_s: float,
                 *, start: str, end: str) -> float | None:
    """% de audiencia que sigue viendo en el segundo `seconds`.

    El informe viene normalizado de 0 a 1 sobre la duracion del video, asi que
    hay que convertir el segundo absoluto a su fraccion antes de buscarlo.
    """
    if not duration_s:
        return None
    try:
        data = _query(
            client,
            ids="channel==MINE",
            start=start,
            end=end,
            dimensions="elapsedVideoTimeRatio",
            metrics="audienceWatchRatio",
            filters=f"video=={video_id}",
        )
    except HttpError:
        return None

    rows = data.get("rows") or []
    if not rows:
        return None

    target = seconds / duration_s
    # La fila mas cercana por debajo del punto que buscamos.
    best = min(rows, key=lambda r: abs(r[0] - target))
    return round(best[1] * 100, 1)


def diagnose(video_ids: list[str] | None = None, *, days: int = 28,
             interactive: bool = True) -> list[VideoDiagnosis]:
    """Diagnostico de los videos del canal en los ultimos `days` dias."""
    yt = auth.youtube(interactive=interactive)
    ya = auth.analytics(interactive=interactive)

    end = date.today()
    start = end - timedelta(days=days)
    start_s, end_s = start.isoformat(), end.isoformat()

    try:
        report = _query(
            ya,
            ids="channel==MINE",
            start=start_s,
            end=end_s,
            dimensions="video",
            metrics=(
                "views,impressions,impressionClickThroughRate,"
                "averageViewPercentage,averageViewDuration,subscribersGained"
            ),
            sort="-views",
            maxResults=50,
        )
    except HttpError as exc:
        raise RuntimeError(
            f"YouTube Analytics rechazo la consulta: {exc}\n"
            "Si el canal es muy nuevo, puede que aun no haya datos que devolver."
        ) from exc

    rows = report.get("rows") or []
    if not rows:
        return []

    ids = [r[0] for r in rows]
    if video_ids:
        ids = [i for i in ids if i in video_ids]

    # Titulos y duraciones, que Analytics no devuelve.
    meta: dict[str, tuple[str, float]] = {}
    details = yt.videos().list(part="snippet,contentDetails", id=",".join(ids)).execute()
    from .youtube import parse_duration

    for item in details.get("items", []):
        meta[item["id"]] = (
            item["snippet"]["title"],
            parse_duration(item["contentDetails"].get("duration", "")),
        )

    out: list[VideoDiagnosis] = []
    for row in rows:
        vid = row[0]
        if vid not in meta:
            continue
        title, duration = meta[vid]
        out.append(
            VideoDiagnosis(
                video_id=vid,
                title=title,
                views=int(row[1]),
                impressions=int(row[2]) if row[2] is not None else None,
                ctr=round(float(row[3]), 2) if row[3] is not None else None,
                avg_view_percentage=round(float(row[4]), 1) if row[4] is not None else None,
                avg_view_duration_s=int(row[5]) if row[5] is not None else None,
                subscribers_gained=int(row[6]) if row[6] is not None else None,
                retention_30s=retention_at(ya, vid, 30, duration, start=start_s, end=end_s),
            )
        )
    return out
