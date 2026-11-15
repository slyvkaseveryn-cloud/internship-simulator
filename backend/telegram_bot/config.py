"""Налаштування: шляхи, токен, ID автора. Значення беруться з bot/.env або змінних середовища."""
import json
import os
from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
ROOT = BOT_DIR.parent.parent  # repository root
CASES_DIR = ROOT / "cases"
DATA_DIR = Path(os.environ.get("DATA_DIR", BOT_DIR / "data"))
DB_PATH = DATA_DIR / "sim.db"


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


_load_env_file(BOT_DIR / ".env")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0") or 0)
REVIEW_SLA_DAYS = 2


def load_cases() -> dict:
    cases = json.loads((CASES_DIR / "cases.json").read_text(encoding="utf-8"))
    for c in cases:
        c["path"] = (ROOT / c["folder"]).resolve()
    return {c["id"]: c for c in cases}


def load_professions() -> dict:
    items = json.loads((CASES_DIR / "professions.json").read_text(encoding="utf-8"))
    return {p["id"]: p for p in items}


CASES = load_cases()
PROFESSIONS = load_professions()
