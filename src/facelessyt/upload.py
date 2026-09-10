"""Subida del video al canal.

Sube SIEMPRE como privado. Publicar es una decision humana: el tooling deja el
video listo en el canal y tu le das al boton cuando lo has visto entero.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from googleapiclient.http import MediaFileUpload

from . import auth

# 5 MB por trozo: permite reanudar sin rehacer la subida entera si se corta.
CHUNK = 5 * 1024 * 1024


@dataclass
class Uploaded:
    video_id: str
    url: str
    privacy: str


def upload(
    video_path: Path,
    *,
    title: str,
    description: str,
    tags: list[str],
    thumbnail: Path | None = None,
    privacy: str = "private",
    category_id: str = "28",  # Science & Technology
    on_progress=None,
) -> Uploaded:
    if not video_path.exists():
        raise FileNotFoundError(video_path)
    if privacy not in {"private", "unlisted", "public"}:
        raise ValueError(f"privacy invalido: {privacy}")

    yt = auth.youtube()

    body = {
        "snippet": {
            "title": title[:100],  # limite duro de YouTube
            "description": description[:5000],
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": "en",
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(str(video_path), chunksize=CHUNK, resumable=True,
                            mimetype="video/mp4")
    request = yt.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = request.next_chunk()
        if status and on_progress:
            on_progress(int(status.progress() * 100))

    video_id = response["id"]

    if thumbnail and thumbnail.exists():
        yt.thumbnails().set(
            videoId=video_id, media_body=MediaFileUpload(str(thumbnail))
        ).execute()

    return Uploaded(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        privacy=privacy,
    )
