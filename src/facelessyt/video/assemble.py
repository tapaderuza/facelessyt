"""Montaje: escenas + narracion -> mp4.

Cada escena se convierte en un clip de imagen fija con su audio. La duracion
del clip la manda el audio, no un numero inventado: dura lo que tarde en
locutarse, mas el `hold` que pida el guion.

Todo pasa por ffmpeg. No hay edicion manual en ningun punto, asi que cambiar
una frase del guion y regenerar el video entero es un solo comando.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import scenes, voice

FPS = 30


class AssembleError(RuntimeError):
    pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise AssembleError(
            f"Fallo: {' '.join(cmd[:6])}...\n{result.stderr.decode('utf-8', 'replace')[-600:]}"
        )
    return result


def audio_duration(path: Path) -> float:
    result = _run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", str(path),
    ])
    return float(json.loads(result.stdout)["format"]["duration"])


@dataclass
class Clip:
    scene_id: str
    video_path: Path
    duration: float
    words: int


def build_scene(scene: dict, workdir: Path, *, engine: str = "auto") -> Clip:
    """Renderiza una escena completa: imagen + voz + clip de video."""
    scene_id = scene["id"]
    narration = scene.get("narration", "").strip()
    hold = float(scene.get("hold", 0.5))

    png = scenes.render(scene, workdir / "frames" / f"{scene_id}.png")
    audio = voice.synthesise(narration, workdir / "audio" / scene_id, engine=engine)
    duration = audio_duration(audio) + hold

    clip = workdir / "clips" / f"{scene_id}.mp4"
    clip.parent.mkdir(parents=True, exist_ok=True)

    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-i", str(png),
        "-i", str(audio),
        # El audio se alarga con silencio hasta cubrir el hold final.
        "-filter_complex", f"[1:a]apad=pad_dur={hold}[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        # Piper entrega 22 kHz mono. YouTube reencodea mejor desde 48 kHz
        # estereo, y un mono de 22 kHz suena delgado en reproduccion normal.
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{duration:.3f}",
        str(clip),
    ])

    return Clip(scene_id, clip, duration, len(narration.split()))


def concat(clips: list[Clip], out_path: Path, workdir: Path) -> Path:
    listing = workdir / "concat.txt"
    # Rutas absolutas: ffmpeg resuelve las relativas contra el directorio del
    # propio listado, no contra el cwd, y acaba duplicando el prefijo.
    listing.write_text(
        "\n".join(f"file '{c.video_path.resolve().as_posix()}'" for c in clips),
        encoding="utf-8",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(out_path),
    ])
    return out_path


def write_chapters(clips: list[Clip], scenes_spec: list[dict], out_path: Path) -> Path:
    """Capitulos con los tiempos REALES del montaje, para pegar en la descripcion.

    Solo se marca capitulo en las escenas que abren seccion (id sin sufijo
    numerico o acabado en -1), que es donde tiene sentido saltar.
    """
    lines, elapsed = [], 0.0
    for clip, spec in zip(clips, scenes_spec):
        base = spec["id"].rsplit("-", 1)
        is_section_start = len(base) == 1 or base[1] in {"1", "quota"}
        if is_section_start:
            mins, secs = divmod(int(elapsed), 60)
            lines.append(f"{mins:02d}:{secs:02d} {spec.get('chapter', base[0])}")
        elapsed += clip.duration

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
