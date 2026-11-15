import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("BOT_TOKEN", "1:test")
os.environ.setdefault("ADMIN_ID", "999")
