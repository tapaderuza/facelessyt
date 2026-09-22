"""Montaje: escenas + narracion -> mp4.

Cada escena se convierte en un clip de imagen con su audio. La duracion del
clip la manda el audio, no un numero inventado: dura lo que tarde en
locutarse, mas el `hold` que pida el guion.

Todo pasa por ffmpeg. No hay edicion manual en ningun punto, asi que cambiar
una frase del guion y regenerar el video entero es un solo comando.

Movimiento (2026-09-18): los cinco primeros videos eran planos fijos de 15 s
de mediana con voz sintetica, y la retencion media fue del 5-12%. El unico
que tenia movimiento continuo retuvo el 22,6%. Asi que ningun fotograma se
queda quieto: cada escena lleva un zoom lento (dentro o fuera, alternando) y
las escenas se encadenan con un fundido corto. No arregla un guion malo, pero
quita la señal de "diapositiva" que hace que la gente se vaya en el primer
minuto.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .. import paidcache
from . import scenes, voice

FPS = 30

# Zoom por escena. 1.08 en ~15 s se nota como movimiento y no como efecto.
ZOOM_MAX = 1.08
# Fundido entre escenas. Mas de 0,3 s emborrona el texto de la siguiente.
XFADE_S = 0.25
# Revelado (2026-09-22): las lineas del terminal aparecen durante este tramo
# del audio de la escena; el resto se queda la imagen completa en pantalla.
# 0.75 deja el ultimo cuarto para que se lea el remate antes del corte.
REVEAL_SHARE = 0.75
# Margen que se añade al ultimo paso. El demuxer de concat redondea cada
# duracion a la base de tiempo del stream y el error se acumula: medido sobre
# las 18 escenas del video 8, los clips salian hasta 1,2 s cortos y el remate
# se perdia. Con el margen, el video siempre sobra y `-t` corta exacto.
REVEAL_TAIL_MARGIN = 1.5
# Musica de fondo, si MUSIC_PATH apunta a un fichero. 0.12 = -18 dB sobre el
# loop (que ya viene a -18 dB de media): queda ~17 dB por debajo de la voz,
# el rango habitual de una cama musical. Se nota que esta; no compite.
MUSIC_GAIN = 0.12


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


def motion_filter(duration: float, index: int, *, width: int = scenes.W,
                  height: int = scenes.H, per_frame: bool = False) -> str:
    """Filtro zoompan para una imagen fija de `duration` segundos.

    Las escenas pares acercan, las impares alejan: dos zooms seguidos en la
    misma direccion se leen como un bucle. La imagen se escala x2 antes del
    zoompan porque el filtro trabaja en enteros y a 1x el zoom tiembla.
    """
    frames = max(1, math.ceil(duration * FPS))
    step = (ZOOM_MAX - 1.0) / frames
    if index % 2 == 0:
        z = f"min(1+{step:.6f}*on,{ZOOM_MAX})"
    else:
        z = f"max({ZOOM_MAX}-{step:.6f}*on,1)"
    # d=1 cuando la entrada ya es un video (secuencia de revelado): cada
    # fotograma de entrada produce uno de salida y `on` avanza con el reloj.
    hold_frames = 1 if per_frame else frames
    return (
        f"scale={width * 2}:{height * 2},"
        f"zoompan=z='{z}':d={hold_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":s={width}x{height}:fps={FPS},format=yuv420p"
    )


def reveal_listing(pngs: list[Path], listing: Path, *, duration: float, hold: float) -> Path:
    """Fichero de concat con una duracion por paso del revelado.

    El ultimo PNG se repite al final porque el demuxer de concat ignora la
    `duration` de la ultima entrada y corta ahi: sin la repeticion, el remate
    de la escena se ve un fotograma. La duracion total del listado supera a
    `duration + hold` a proposito (REVEAL_TAIL_MARGIN); quien corta es `-t`.
    """
    steps = len(pngs)
    per = duration * REVEAL_SHARE / steps
    rest = duration * (1 - REVEAL_SHARE) + hold + REVEAL_TAIL_MARGIN
    rows = []
    for png in pngs:
        rows.append(f"file '{png.resolve().as_posix()}'")
        rows.append(f"duration {per:.3f}")
    rows.append(f"file '{pngs[-1].resolve().as_posix()}'")
    rows.append(f"duration {rest:.3f}")
    rows.append(f"file '{pngs[-1].resolve().as_posix()}'")
    listing.parent.mkdir(parents=True, exist_ok=True)
    listing.write_text("\n".join(rows), encoding="utf-8")
    return listing


def encode_still(png: Path | list[Path], audio: Path, clip: Path, *, duration: float,
                 hold: float, index: int = 0, motion: bool = True) -> Path:
    """Imagen (o secuencia de revelado) + audio -> clip.

    Separado de build_scene para poder probarlo sin TTS.
    """
    pngs = [png] if isinstance(png, Path) else list(png)
    clip.parent.mkdir(parents=True, exist_ok=True)

    if len(pngs) > 1:
        listing = reveal_listing(pngs, clip.with_suffix(".seq.txt"),
                                 duration=duration - hold, hold=hold)
        video_in = ["-f", "concat", "-safe", "0", "-i", str(listing)]
        # fps=30 antes del zoom: el demuxer de concat entrega frames a ritmo
        # variable y zoompan cuenta fotogramas de salida, no segundos.
        zoom = motion_filter(duration, index, per_frame=True)
        vfilter = f"[0:v]fps={FPS},{zoom}[v]" if motion else f"[0:v]fps={FPS},format=yuv420p[v]"
    elif motion:
        video_in = ["-i", str(pngs[0])]
        vfilter = f"[0:v]{motion_filter(duration, index)}[v]"
    else:
        video_in = ["-loop", "1", "-i", str(pngs[0])]
        vfilter = "[0:v]format=yuv420p[v]"

    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        *video_in,
        "-i", str(audio),
        # El audio se alarga con silencio hasta cubrir el hold final.
        "-filter_complex", f"{vfilter};[1:a]apad=pad_dur={hold}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        # Piper entrega 22 kHz mono. YouTube reencodea mejor desde 48 kHz
        # estereo, y un mono de 22 kHz suena delgado en reproduccion normal.
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
        "-t", f"{duration:.3f}",
        str(clip),
    ])
    return clip


def cached_engine(workdir: Path) -> str | None:
    """Motor con el que se locuto este episodio, segun los marcadores del cache.

    Devuelve None si aun no hay audio. Si hay marcadores de varios motores,
    devuelve el del primero que aparezca: basta para detectar el cambio.
    """
    for marker in sorted((workdir / "audio").glob("*.key.json")):
        try:
            key = json.loads(marker.read_text(encoding="utf-8")).get("key", "")
        except (json.JSONDecodeError, OSError):
            continue
        if key:
            return key.split("|", 1)[0]
    return None


class VoiceChangeError(AssembleError):
    """Re-locutar un episodio ya renderizado con otro motor de voz.

    Paso de verdad el 2026-09-22: un `docker run` sin las variables de
    ElevenLabs hizo que `--engine auto` cayera a Piper y el episodio 8 se
    volviera a locutar entero con otra voz, sin un solo aviso. El video ya
    estaba subido con la voz buena. Cambiar de voz es legitimo; hacerlo sin
    querer, no.
    """


def check_engine(workdir: Path, engine: str, *, allow_change: bool = False) -> str:
    """Motor que se va a usar. Revienta si cambia el de un episodio ya locutado."""
    resolved = voice.resolve_engine(engine)
    previous = cached_engine(workdir)
    if previous and previous != resolved and not allow_change:
        raise VoiceChangeError(
            f"Este episodio esta locutado con '{previous}' y ahora se usaria "
            f"'{resolved}'.\n"
            + ("Falta ELEVENLABS_API_KEY en el entorno del render.\n"
               if resolved == "piper" else "")
            + "Si el cambio de voz es intencionado, usa --allow-voice-change."
        )
    return resolved


def _cached_voice(narration: str, base: Path, *, engine: str) -> Path:
    """Sintetiza solo si texto o voz cambiaron. Con ElevenLabs cada llamada
    cuesta creditos; reintentar un montaje no debe volver a pagar las escenas."""
    key = voice.fingerprint(engine) + "|" + narration
    return paidcache.once(
        base.with_suffix(".key.json"), key,
        lambda: voice.synthesise(narration, base, engine=engine),
    )


def build_scene(scene: dict, workdir: Path, *, engine: str = "auto",
                index: int = 0, motion: bool = True, reveal: bool = True) -> Clip:
    """Renderiza una escena completa: imagen + voz + clip de video."""
    scene_id = scene["id"]
    narration = scene.get("narration", "").strip()
    hold = float(scene.get("hold", 0.5))

    frames = (scenes.render_reveal(scene, workdir / "frames", scene_id) if reveal
              else [scenes.render(scene, workdir / "frames" / f"{scene_id}.png")])
    audio = _cached_voice(narration, workdir / "audio" / scene_id, engine=engine)
    duration = audio_duration(audio) + hold

    clip = workdir / "clips" / f"{scene_id}.mp4"
    encode_still(frames, audio, clip, duration=duration, hold=hold, index=index, motion=motion)
    return Clip(scene_id, clip, duration, len(narration.split()))


def _concat_copy(clips: list[Clip], out_path: Path, workdir: Path) -> Path:
    listing = workdir / "concat.txt"
    # Rutas absolutas: ffmpeg resuelve las relativas contra el directorio del
    # propio listado, no contra el cwd, y acaba duplicando el prefijo.
    listing.write_text(
        "\n".join(f"file '{c.video_path.resolve().as_posix()}'" for c in clips),
        encoding="utf-8",
    )
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(listing),
        "-c", "copy", str(out_path),
    ])
    return out_path


# Clips por pasada de xfade. ffmpeg abre y decodifica todos los inputs a la
# vez; con 24 clips de 1080p el contenedor se quedo sin memoria en el montaje
# del video 6. Por bloques, el maximo abierto es este numero.
XFADE_BATCH = 8


def _concat_xfade(clips: list[Clip], out_path: Path) -> Path:
    """Encadena con fundidos, por bloques. Cada fundido come XFADE_S del total."""
    if len(clips) > XFADE_BATCH:
        partials = []
        for i in range(0, len(clips), XFADE_BATCH):
            chunk = clips[i:i + XFADE_BATCH]
            part = out_path.with_name(f"{out_path.stem}.part{i // XFADE_BATCH}.mp4")
            if len(chunk) == 1:
                part = chunk[0].video_path
            else:
                _concat_xfade_once(chunk, part)
            dur = sum(c.duration for c in chunk) - XFADE_S * (len(chunk) - 1)
            partials.append(Clip(f"part{i}", part, dur, sum(c.words for c in chunk)))
        return _concat_xfade(partials, out_path)
    return _concat_xfade_once(clips, out_path)


def _concat_xfade_once(clips: list[Clip], out_path: Path) -> Path:
    inputs = []
    for c in clips:
        inputs += ["-i", str(c.video_path)]

    parts, elapsed = [], 0.0
    prev_v, prev_a = "[0:v]", "[0:a]"
    for i in range(1, len(clips)):
        elapsed += clips[i - 1].duration - XFADE_S
        out_v, out_a = f"[v{i}]", f"[a{i}]"
        parts.append(
            f"{prev_v}[{i}:v]xfade=transition=fade:duration={XFADE_S}:offset={elapsed:.3f}{out_v}"
        )
        parts.append(f"{prev_a}[{i}:a]acrossfade=d={XFADE_S}{out_a}")
        prev_v, prev_a = out_v, out_a

    _run([
        "ffmpeg", "-y", "-loglevel", "error", *inputs,
        "-filter_complex", ";".join(parts),
        "-map", prev_v, "-map", prev_a,
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        str(out_path),
    ])
    return out_path


def add_music(video: Path, music: Path, out_path: Path) -> Path:
    """Mezcla musica en bucle bajo la voz, con fundido de salida."""
    total = audio_duration(video)
    fade_start = max(0.0, total - 3.0)
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video),
        "-stream_loop", "-1", "-i", str(music),
        "-filter_complex",
        f"[1:a]volume={MUSIC_GAIN},afade=t=out:st={fade_start:.3f}:d=3[m];"
        "[0:a][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total:.3f}",
        str(out_path),
    ])
    return out_path


def concat(clips: list[Clip], out_path: Path, workdir: Path, *,
           transitions: bool = True, music: Path | None = None) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if music is None and os.getenv("MUSIC_PATH", "").strip():
        music = Path(os.environ["MUSIC_PATH"])
    if music is not None and not music.exists():
        raise AssembleError(f"MUSIC_PATH no existe: {music}")

    joined = workdir / "joined.mp4" if music else out_path
    if transitions and len(clips) > 1:
        _concat_xfade(clips, joined)
    else:
        _concat_copy(clips, joined, workdir)

    if music:
        add_music(joined, music, out_path)
    return out_path


def write_chapters(clips: list[Clip], scenes_spec: list[dict], out_path: Path,
                   *, transitions: bool = True) -> Path:
    """Capitulos con los tiempos REALES del montaje, para pegar en la descripcion.

    Una escena abre capitulo si declara `chapter`. Deducirlo del sufijo del id
    era fragil: dejaba fuera secciones cuyo id no acababa en -1, y colaba ids
    internos ("bug-investigation", "cost") como titulo de capitulo.

    Si el guion no declara ninguno, se cae al heuristico anterior para no dejar
    la descripcion sin capitulos.
    """
    declara_capitulos = any(s.get("chapter") for s in scenes_spec)
    # Con fundidos, cada escena empieza XFADE_S antes de que acabe la anterior.
    overlap = XFADE_S if transitions else 0.0

    lines, elapsed = [], 0.0
    for clip, spec in zip(clips, scenes_spec):
        if declara_capitulos:
            titulo = spec.get("chapter")
        else:
            base = spec["id"].rsplit("-", 1)
            titulo = base[0] if (len(base) == 1 or base[1] in {"1", "quota"}) else None

        if titulo:
            mins, secs = divmod(int(elapsed), 60)
            lines.append(f"{mins:02d}:{secs:02d} {titulo}")
        elapsed += clip.duration - overlap

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path
