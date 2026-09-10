"""Carga de configuracion desde .env y del fichero de nicho."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

def _detect_root() -> Path:
    """Raiz del proyecto: donde viven niches/ y data/.

    No se puede deducir subiendo desde __file__ y ya esta: eso solo vale con el
    repo clonado (src/facelessyt/config.py -> raiz). Cuando el paquete esta
    instalado en site-packages, como dentro del contenedor, apunta al directorio
    de Python. Por eso hay tres casos, en orden:
    """
    override = os.getenv("FACELESSYT_ROOT", "").strip()
    if override:
        return Path(override)

    repo_root = Path(__file__).resolve().parents[2]
    if (repo_root / "niches").is_dir():
        return repo_root

    return Path.cwd()


ROOT = _detect_root()
DATA_DIR = ROOT / "data"
NICHES_DIR = ROOT / "niches"

load_dotenv(ROOT / ".env")


class ConfigError(RuntimeError):
    """Falta configuracion necesaria para ejecutar."""


def api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY", "").strip()
    if not key:
        raise ConfigError(
            "Falta YOUTUBE_API_KEY.\n"
            "  1. Copia .env.example a .env\n"
            "  2. Crea una clave en https://console.cloud.google.com/ "
            "(YouTube Data API v3 -> Credenciales -> Clave de API)\n"
            "  3. Pegala en .env"
        )
    return key


def my_channel_id() -> str:
    cid = os.getenv("MY_CHANNEL_ID", "").strip()
    if not cid:
        raise ConfigError("Falta MY_CHANNEL_ID en .env (el ID de tu canal, empieza por UC...).")
    return cid


def load_niche(name: str) -> dict:
    path = NICHES_DIR / f"{name}.yaml"
    if not path.exists():
        available = sorted(p.stem for p in NICHES_DIR.glob("*.yaml"))
        raise ConfigError(
            f"No existe el nicho '{name}' ({path}).\n"
            f"Disponibles: {', '.join(available) if available else '(ninguno)'}"
        )
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    data.setdefault("name", name)
    data.setdefault("seed_channels", [])
    data.setdefault("keywords", [])
    return data
