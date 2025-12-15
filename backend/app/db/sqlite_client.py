import sqlite3
import sys
from pathlib import Path


def _resolve_db_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "bili_note.db"

    backend_dir = Path(__file__).resolve().parents[2]
    project_root = backend_dir.parent

    candidates = [
        project_root / "bili_note.db",
        backend_dir / "bili_note.db",
    ]

    for p in candidates:
        if p.exists():
            return p

    return backend_dir / "bili_note.db"

def get_connection():
    return sqlite3.connect(str(_resolve_db_path()))
