"""Narracion: texto -> wav.

Dos motores. Piper es local y gratuito, y es el que se usa por defecto: no
depende de ninguna cuenta ni consume credito, asi que se puede regenerar el
video entero las veces que haga falta. ElevenLabs da mejor voz y se activa
solo si hay clave en el entorno.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


class VoiceError(RuntimeError):
    pass


# Ritmo de Piper (piper-tts 1.8, voz Lessac medium), medido en el contenedor
# con un parrafo de 38 palabras el 2026-09-18:
#   sin flags                 12,9 s  -> ~176 palabras/min
#   length_scale 0.85 + 0.1 s 12,3 s  -> ~185 palabras/min
#   length_scale 0.80 + 0 s   10,9 s  -> ~210 palabras/min
# La escala no es lineal y cada sintesis varia unas decimas. 0.85 quita la
# cadencia de "lectura"; escucha una escena antes de bajar mas. sentence_silence vale 0 por
# defecto en esta version; 0,1 s deja respirar entre frases.
PIPER_LENGTH_SCALE = float(os.getenv("PIPER_LENGTH_SCALE", "0.85"))
PIPER_SENTENCE_SILENCE = float(os.getenv("PIPER_SENTENCE_SILENCE", "0.1"))


def _normalise(text: str) -> str:
    """Limpia el texto para que el TTS no lo lea raro."""
    text = " ".join(text.split())
    # Los guiones largos se leen como pausa, no como palabra.
    return text.replace("—", ", ").replace("–", ", ")


def _piper(text: str, out_path: Path) -> Path:
    voice = os.getenv("PIPER_VOICE", "").strip()
    if not voice or not Path(voice).exists():
        raise VoiceError(
            f"No se encuentra la voz de Piper ({voice or 'PIPER_VOICE sin definir'}). "
            "Ejecuta el render dentro de la imagen facelessyt-video, que ya la trae."
        )
    if not shutil.which("piper"):
        raise VoiceError("El binario 'piper' no esta en el PATH. Usa la imagen de video.")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            "piper", "--model", voice, "--output_file", str(out_path),
            "--length_scale", f"{PIPER_LENGTH_SCALE:g}",
            "--sentence_silence", f"{PIPER_SENTENCE_SILENCE:g}",
        ],
        input=_normalise(text).encode("utf-8"),
        capture_output=True,
    )
    if result.returncode != 0 or not out_path.exists():
        raise VoiceError(f"piper fallo: {result.stderr.decode('utf-8', 'replace')[:300]}")
    return out_path


def _elevenlabs(text: str, out_path: Path) -> Path:
    import requests

    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "").strip()
    if not voice_id:
        raise VoiceError("Falta ELEVENLABS_VOICE_ID en el entorno.")

    response = requests.post(
        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        headers={"xi-api-key": key, "Content-Type": "application/json"},
        json={
            "text": _normalise(text),
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {"stability": 0.45, "similarity_boost": 0.75},
        },
        timeout=120,
    )
    if not response.ok:
        raise VoiceError(f"ElevenLabs {response.status_code}: {response.text[:200]}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(response.content)
    return out_path


def resolve_engine(engine: str = "auto") -> str:
    if engine == "auto":
        return "elevenlabs" if os.getenv("ELEVENLABS_API_KEY", "").strip() else "piper"
    return engine


def fingerprint(engine: str = "auto") -> str:
    """Todo lo que, ademas del texto, cambia el audio. Va en la clave del cache:
    con solo el texto, cambiar de voz devolvia el audio de la voz anterior."""
    engine = resolve_engine(engine)
    if engine == "elevenlabs":
        return f"elevenlabs|{os.getenv('ELEVENLABS_VOICE_ID', '').strip()}|eleven_multilingual_v2|0.45|0.75"
    return (f"piper|{Path(os.getenv('PIPER_VOICE', '')).name}|"
            f"ls{PIPER_LENGTH_SCALE:g}|ss{PIPER_SENTENCE_SILENCE:g}")


def synthesise(text: str, out_path: Path, *, engine: str = "auto") -> Path:
    """Genera el audio de una escena. Devuelve la ruta del fichero."""
    engine = resolve_engine(engine)

    if engine == "piper":
        return _piper(text, out_path.with_suffix(".wav"))
    if engine == "elevenlabs":
        return _elevenlabs(text, out_path.with_suffix(".mp3"))
    raise VoiceError(f"Motor de voz desconocido: {engine}")
