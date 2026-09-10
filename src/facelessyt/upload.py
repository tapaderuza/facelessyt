"""Subida del video al canal.

Sube SIEMPRE como privado. Publicar es una decision humana: el tooling deja el
video listo en el canal y tu le das al boton cuando lo has visto entero.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from . import auth

# 5 MB por trozo: permite reanudar sin rehacer la subida entera si se corta.
CHUNK = 5 * 1024 * 1024


@dataclass
class Uploaded:
    video_id: str
    url: str
    privacy: str
    thumbnail_error: str | None = None


class PreflightError(RuntimeError):
    """El canal no puede aceptar este video. Mejor saberlo antes de subirlo."""


UNVERIFIED_LIMIT_S = 15 * 60


def _duration_seconds(video_path: Path) -> float | None:
    """Duracion via ffprobe. None si ffprobe no esta disponible."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format",
             str(video_path)],
            capture_output=True, timeout=60,
        )
        return float(json.loads(out.stdout)["format"]["duration"])
    except (FileNotFoundError, KeyError, ValueError, subprocess.SubprocessError):
        return None


def preflight(yt, video_path: Path) -> None:
    """Comprueba antes de subir lo que YouTube solo te dira despues.

    Un canal sin verificar tiene el limite en 15 minutos. Si te pasas, YouTube
    acepta la subida entera, la procesa a medias, y luego la descarta con un
    "Processing abandoned" que solo se ve en Studio: por la API el video
    simplemente desaparece. Cuarenta megas y diez minutos tirados.
    """
    duration = _duration_seconds(video_path)
    if duration is None or duration <= UNVERIFIED_LIMIT_S:
        return

    status = yt.channels().list(part="status", mine=True).execute()
    long_uploads = (status.get("items") or [{}])[0].get("status", {}).get(
        "longUploadsStatus"
    )
    if long_uploads == "allowed":
        return

    raise PreflightError(
        f"El video dura {duration / 60:.1f} min y este canal tiene el limite en 15.\n"
        f"longUploadsStatus = {long_uploads!r}\n\n"
        "Verifica el canal en https://www.youtube.com/verify (pide un telefono).\n"
        "Esa misma verificacion desbloquea las miniaturas personalizadas."
    )


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
    preflight(yt, video_path)

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

    # A partir de aqui el video YA existe en el canal. Nada de lo que siga puede
    # tumbar la funcion sin devolver el id: perderlo obliga a buscarlo a mano y,
    # peor, invita a reintentar la subida y acabar con un duplicado.
    thumbnail_error: str | None = None
    if thumbnail and thumbnail.exists():
        try:
            yt.thumbnails().set(
                videoId=video_id, media_body=MediaFileUpload(str(thumbnail))
            ).execute()
        except HttpError as exc:
            if exc.resp.status == 403:
                thumbnail_error = (
                    "YouTube rechaza miniaturas personalizadas en canales sin "
                    "verificar. Verifica el canal en youtube.com/verify (pide un "
                    "telefono) y vuelve a intentarlo con 'facelessyt thumbnail'."
                )
            else:
                thumbnail_error = str(exc)

    return Uploaded(
        video_id=video_id,
        url=f"https://www.youtube.com/watch?v={video_id}",
        privacy=privacy,
        thumbnail_error=thumbnail_error,
    )


def set_thumbnail(video_id: str, thumbnail: Path) -> None:
    """Pone la miniatura de un video ya subido.

    Existe aparte porque la verificacion del canal suele llegar despues de la
    primera subida, y no hay que resubir el video para arreglar eso.
    """
    if not thumbnail.exists():
        raise FileNotFoundError(thumbnail)
    auth.youtube().thumbnails().set(
        videoId=video_id, media_body=MediaFileUpload(str(thumbnail))
    ).execute()


def publish(video_id: str, *, privacy: str = "public") -> str:
    """Cambia la visibilidad de un video ya subido.

    Separado de upload() a proposito: subir es rutina, publicar es una decision.
    Un script que pudiera hacer ambas cosas de una vez acabaria haciendo publico
    algo por accidente algun dia.
    """
    if privacy not in {"private", "unlisted", "public"}:
        raise ValueError(f"privacy invalido: {privacy}")

    yt = auth.youtube()
    yt.videos().update(
        part="status",
        body={"id": video_id, "status": {"privacyStatus": privacy}},
    ).execute()
    return f"https://www.youtube.com/watch?v={video_id}"
