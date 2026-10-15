"""Where the app finds its bundled data files (practice DB, lessons)."""
from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the folder that holds ``data/``.

    Works both when running from source and when frozen by PyInstaller.
    """
    if getattr(sys, "frozen", False):
        # PyInstaller unpacks bundled data next to the executable.
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    return project_root() / "data"


def practice_db_path() -> Path:
    return data_dir() / "practice" / "shop.db"


def lessons_dir() -> Path:
    return data_dir() / "lessons"
