"""Una llamada de pago dentro de un bucle de reintentos se paga en cada intento.

El 2026-09-18 el montaje del video 6 fallo en el ultimo paso (ffmpeg sin
memoria) despues de sintetizar 24 escenas con ElevenLabs: 4.177 creditos, el
13,9% del plan mensual. Reintentar el render habria vuelto a pagar las 24.

La regla: el resultado de una llamada de pago se guarda junto a una clave que
incluye TODO lo que cambia el resultado (texto, motor, voz, modelo, velocidad).
Si la clave coincide, se devuelve el fichero; si no, se paga una vez y se
apunta. Doce lineas. Vale para TTS, generacion de imagenes y llamadas a LLM.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


def once(marker: Path, key: str, produce: Callable[[], Path]) -> Path:
    """Ejecuta `produce` solo si no hay ya un resultado apuntado para `key`.

    `marker` es un JSON al lado del resultado con la clave y la ruta. Si la
    clave cambia (otra voz, otro texto) se vuelve a producir; si el fichero
    apuntado ha desaparecido, tambien.
    """
    if marker.exists():
        record = json.loads(marker.read_text(encoding="utf-8"))
        if record.get("key") == key and Path(record.get("path", "")).exists():
            return Path(record["path"])
    result = produce()
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"key": key, "path": str(result)}), encoding="utf-8")
    return result
