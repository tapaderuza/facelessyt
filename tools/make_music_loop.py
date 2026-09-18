"""Genera el loop de musica de fondo del canal. Sin samples, sin licencias.

    .venv/Scripts/python.exe tools/make_music_loop.py            -> data/music/loop.wav (+ .mp3 si hay ffmpeg)

Por que sintetizarlo en vez de bajar un mp3: cualquier pista de terceros trae
una licencia que hay que leer, atribuir o pagar, y YouTube hace content-ID
sobre muchas "royalty free". Un pad generado por este script es nuestro por
construccion y suena igual en cada render.

Que suena: un pad de cuatro acordes (Am - F - C - G) en registro grave, con
ataque lento, dos octavas, un poco de vibrato y un pulso sordo cada negra a
84 bpm. Esta pensado para ir a -26 dB bajo la voz (assemble.MUSIC_GAIN), no
para escucharse solo. Se mezcla en bucle, asi que el final enlaza con el
principio sin corte.
"""

from __future__ import annotations

import math
import shutil
import subprocess
import wave
from array import array
from pathlib import Path

RATE = 44100
BPM = 84
BEATS_PER_CHORD = 8          # dos compases de 4/4 por acorde
CHORDS = [                   # frecuencias fundamentales (Hz), voicing cerrado
    (110.00, 130.81, 164.81),  # A2 C3 E3   (Am)
    (87.31, 110.00, 130.81),   # F2 A2 C3   (F)
    (98.00, 130.81, 164.81),   # G2 C3 E3   (C/G)
    (98.00, 123.47, 146.83),   # G2 B2 D3   (G)
]
OUT = Path(__file__).resolve().parents[1] / "data" / "music"


def _pad(freq: float, t: float, chord_t: float, chord_len: float) -> float:
    """Una voz del pad: fundamental + octava + quinta suave, con vibrato."""
    vib = 1.0 + 0.0025 * math.sin(2 * math.pi * 4.7 * t)
    f = freq * vib
    s = (math.sin(2 * math.pi * f * t)
         + 0.45 * math.sin(2 * math.pi * 2 * f * t)
         + 0.20 * math.sin(2 * math.pi * 3 * f * t))
    # Envolvente por acorde: ataque 0,8 s, caida suave al final para que el
    # cambio de acorde no haga clic.
    attack = min(1.0, chord_t / 0.8)
    release = min(1.0, (chord_len - chord_t) / 0.6)
    return s * attack * release


def _pulse(beat_t: float) -> float:
    """Pulso sordo (80 Hz, 90 ms) al principio de cada negra."""
    if beat_t > 0.09:
        return 0.0
    env = (1 - beat_t / 0.09) ** 2
    return env * math.sin(2 * math.pi * 80 * beat_t)


def render() -> array:
    beat = 60 / BPM
    chord_len = beat * BEATS_PER_CHORD
    total = chord_len * len(CHORDS)
    n = int(total * RATE)
    out = array("h", [0]) * n
    for i in range(n):
        t = i / RATE
        ci = int(t // chord_len) % len(CHORDS)
        chord_t = t - ci * chord_len
        beat_t = t % beat
        v = sum(_pad(f, t, chord_t, chord_len) for f in CHORDS[ci]) / 6.0
        v += 0.35 * _pulse(beat_t)
        # Un poco de aire: ruido muy bajo, filtrado por promedio.
        out[i] = int(max(-1.0, min(1.0, v * 0.6)) * 32767)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wav = OUT / "loop.wav"
    pcm = render()
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(pcm.tobytes())
    print(f"{wav}  ({len(pcm) / RATE:.1f} s)")

    if shutil.which("ffmpeg"):
        mp3 = OUT / "loop.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav),
                        "-af", "lowpass=f=2400", "-b:a", "128k", str(mp3)], check=True)
        print(mp3)


if __name__ == "__main__":
    main()
