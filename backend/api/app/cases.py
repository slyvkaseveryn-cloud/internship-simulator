"""Case and profession metadata, bundled into the Lambda zip under cases/ (see infra/api.tf)."""
import json
from functools import cache
from pathlib import Path

_HERE = Path(__file__).resolve().parent
# In Lambda: /var/task/app + /var/task/cases. In the repo: backend/api/app + <root>/cases.
_CANDIDATES = [_HERE.parent / "cases", _HERE.parents[2] / "cases"]


def _dir() -> Path:
    for d in _CANDIDATES:
        if (d / "cases.json").exists():
            return d
    raise FileNotFoundError("cases/cases.json not found")


@cache
def cases() -> dict[str, dict]:
    return {c["id"]: c for c in json.loads((_dir() / "cases.json").read_text(encoding="utf-8"))}


@cache
def professions() -> dict[str, dict]:
    return {p["id"]: p for p in json.loads((_dir() / "professions.json").read_text(encoding="utf-8"))}
