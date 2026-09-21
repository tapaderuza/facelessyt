"""Hook de Claude Code: el agente no puede guardar un guion que no pase el lint.

Se registra en .claude/settings.json como PostToolUse de Edit|Write. Claude
Code le pasa por stdin un JSON con `tool_input.file_path`; si es un guion de
scripts/*.yaml, ejecuta `facelessyt.video check` sobre el. Con errores, sale
con codigo 2: Claude Code le devuelve el stderr al agente y este tiene que
arreglarlos antes de seguir. Cualquier otro fichero: exit 0, sin ruido.

Por que existe: el lint ya paraba `render`, pero el agente que escribe el
guion solo se enteraba al final, tras escribir 24 escenas. Con el hook se
entera en la misma edicion. Es el mismo harness, un paso antes.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / ".venv" / "Scripts" / "python.exe"


def target_from_stdin() -> Path | None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return None
    raw = (payload.get("tool_input") or {}).get("file_path", "")
    if not raw:
        return None
    path = Path(raw)
    if path.suffix.lower() not in {".yaml", ".yml"}:
        return None
    try:
        path.resolve().relative_to((ROOT / "scripts").resolve())
    except ValueError:
        return None
    return path


def main() -> int:
    path = target_from_stdin()
    if path is None or not path.exists():
        return 0
    python = str(PY) if PY.exists() else sys.executable
    result = subprocess.run(
        [python, "-m", "facelessyt.video", "check", "--script", str(path)],
        capture_output=True, text=True, cwd=ROOT,
    )
    if result.returncode == 0:
        return 0
    sys.stderr.write(
        f"[facelessyt lint] {path.name} no pasa el lint de gancho/ritmo. "
        "Arregla estos errores antes de seguir:\n" + result.stdout + result.stderr
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
