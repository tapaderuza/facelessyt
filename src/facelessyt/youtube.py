"""Cliente minimo de la YouTube Data API v3 con contabilidad de cuota.

La cuota diaria gratuita es de 10.000 unidades. Los costes por llamada son:
  channels.list       1
  playlistItems.list  1
  videos.list         1
  search.list       100   <-- caro, se usa solo para descubrir canales nuevos

Por eso la estrategia por defecto es partir de canales semilla y recorrer su
playlist de subidas (1 unidad por cada 50 videos) en vez de usar search.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import requests

API = "https://www.googleapis.com/youtube/v3"

QUOTA_COST = {
    "channels": 1,
    "playlistItems": 1,
    "videos": 1,
    "search": 100,
}

_DURATION_RE = re.compile(
    r"^P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def parse_duration(iso: str) -> int:
    """Convierte una duracion ISO-8601 de YouTube (p.ej. 'PT12M31S') a segundos."""
    match = _DURATION_RE.match(iso or "")
    if not match:
        return 0
    parts = {k: int(v) for k, v in match.groupdict(default="0").items()}
    return parts["days"] * 86400 + parts["hours"] * 3600 + parts["minutes"] * 60 + parts["seconds"]


def parse_published(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def age_days(published: datetime) -> float:
    return (datetime.now(timezone.utc) - published).total_seconds() / 86400


class YouTubeError(RuntimeError):
    pass


@dataclass
class Video:
    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published: datetime
    views: int
    likes: int
    comments: int
    duration_s: int

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.video_id}"

    @property
    def age_days(self) -> float:
        return age_days(self.published)

    @property
    def is_short(self) -> bool:
        return self.duration_s <= 120


@dataclass
class Channel:
    channel_id: str
    title: str
    handle: str | None
    subscribers: int | None  # None si el canal los oculta
    video_count: int
    uploads_playlist: str


@dataclass
class Client:
    key: str
    quota_used: int = 0
    _session: requests.Session = field(default_factory=requests.Session)

    def _get(self, resource: str, **params) -> dict:
        params["key"] = self.key
        response = self._session.get(f"{API}/{resource}", params=params, timeout=30)
        self.quota_used += QUOTA_COST.get(resource, 1)

        if response.status_code == 403:
            body = response.json().get("error", {})
            reason = (body.get("errors") or [{}])[0].get("reason", "")
            if reason in {"quotaExceeded", "dailyLimitExceeded"}:
                raise YouTubeError(
                    "Cuota diaria de la API agotada (10.000 unidades). "
                    "Se reinicia a medianoche hora del Pacifico."
                )
            raise YouTubeError(f"403 de la API ({reason}): {body.get('message', '')}")
        if not response.ok:
            raise YouTubeError(f"{response.status_code} en {resource}: {response.text[:300]}")
        return response.json()

    # -- canales ---------------------------------------------------------

    def resolve_channel(self, ref: str) -> Channel | None:
        """Resuelve un canal por handle ('@nombre'), ID ('UC...') o URL. None si no existe."""
        ref = ref.strip()
        if "youtube.com" in ref:
            ref = ref.rstrip("/").split("/")[-1]

        if ref.startswith("UC") and len(ref) == 24:
            params = {"id": ref}
        else:
            params = {"forHandle": ref if ref.startswith("@") else f"@{ref}"}

        data = self._get(
            "channels", part="snippet,statistics,contentDetails", **params
        )
        items = data.get("items") or []
        if not items:
            return None

        item = items[0]
        stats = item.get("statistics", {})
        hidden = stats.get("hiddenSubscriberCount", False)
        return Channel(
            channel_id=item["id"],
            title=item["snippet"]["title"],
            handle=item["snippet"].get("customUrl"),
            subscribers=None if hidden else int(stats.get("subscriberCount", 0)),
            video_count=int(stats.get("videoCount", 0)),
            uploads_playlist=item["contentDetails"]["relatedPlaylists"]["uploads"],
        )

    # -- videos ----------------------------------------------------------

    def recent_video_ids(self, uploads_playlist: str, limit: int = 60) -> list[str]:
        """IDs de las ultimas subidas de un canal, de mas nueva a mas antigua."""
        ids: list[str] = []
        page_token = None
        while len(ids) < limit:
            data = self._get(
                "playlistItems",
                part="contentDetails",
                playlistId=uploads_playlist,
                maxResults=min(50, limit - len(ids)),
                **({"pageToken": page_token} if page_token else {}),
            )
            ids.extend(i["contentDetails"]["videoId"] for i in data.get("items", []))
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return ids[:limit]

    def videos(self, video_ids: list[str]) -> list[Video]:
        """Detalle de videos. Agrupa de 50 en 50 (1 unidad de cuota por lote)."""
        out: list[Video] = []
        for start in range(0, len(video_ids), 50):
            batch = video_ids[start : start + 50]
            data = self._get(
                "videos", part="snippet,statistics,contentDetails", id=",".join(batch)
            )
            for item in data.get("items", []):
                stats = item.get("statistics", {})
                out.append(
                    Video(
                        video_id=item["id"],
                        title=item["snippet"]["title"],
                        channel_id=item["snippet"]["channelId"],
                        channel_title=item["snippet"]["channelTitle"],
                        published=parse_published(item["snippet"]["publishedAt"]),
                        views=int(stats.get("viewCount", 0)),
                        likes=int(stats.get("likeCount", 0)),
                        comments=int(stats.get("commentCount", 0)),
                        duration_s=parse_duration(item["contentDetails"].get("duration", "")),
                    )
                )
        return out

    def search_channels(self, query: str, limit: int = 10) -> list[str]:
        """Descubre canales por palabra clave. CUESTA 100 UNIDADES por llamada."""
        data = self._get(
            "search", part="snippet", q=query, type="channel", maxResults=min(50, limit)
        )
        return [i["snippet"]["channelId"] for i in data.get("items", [])]
