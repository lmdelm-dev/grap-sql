"""User settings that survive a restart.

Kept deliberately simple: one small JSON file next to the progress database.
If it is missing or damaged we fall back to sensible defaults instead of
crashing, so a non-coder can always just start the app.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path

APP_DIRNAME = ".grap-sql"
LEGACY_DIRNAME = ".sql_terminal_school"   # pre-rebrand name; migrated on first run


def app_dir() -> Path:
    """Folder where the app keeps settings, progress and backups."""
    override = os.environ.get("GRAPSQL_DIR") or os.environ.get("SQLSCHOOL_DIR")
    if override:
        return Path(override)
    base = Path.home()
    new_dir = base / APP_DIRNAME
    legacy = base / LEGACY_DIRNAME
    # Seamless upgrade: quietly adopt an older install's folder so no progress
    # is ever lost just because the app got a new name.
    if not new_dir.exists() and legacy.exists():
        try:
            legacy.rename(new_dir)
        except OSError:
            return legacy
    return new_dir


SETTINGS_PATH = app_dir() / "settings.json"

# Sensible defaults, also used for a brand-new install.
DEFAULTS = {
    "theme": "dark",
    "font_size": 15,
    "reduce_motion": False,
    "pro_mode": False,
    "type_along": True,
    "learner_name": "",
    "onboarded": False,
    "daily_session_length": 20,
    "window_w": 1280,
    "window_h": 820,
    "vsplit": [420, 400],          # teacher | right column
    "hsplit": [300, 260],          # type | output
    "last_lesson": 1,
    "last_step": 0,
}


@dataclass
class Settings:
    theme: str = "dark"
    font_size: int = 15
    reduce_motion: bool = False
    pro_mode: bool = False
    type_along: bool = True
    learner_name: str = ""
    onboarded: bool = False
    daily_session_length: int = 20
    window_w: int = 1280
    window_h: int = 820
    vsplit: list = None
    hsplit: list = None
    last_lesson: int = 1
    last_step: int = 0

    def __post_init__(self):
        for key in ("vsplit", "hsplit"):
            if getattr(self, key) is None:
                setattr(self, key, list(DEFAULTS[key]))

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def load(cls, path: Path | None = None) -> "Settings":
        path = path or SETTINGS_PATH
        data: dict = {}
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    data = {}
        except Exception:
            data = {}
        known = {f.name for f in fields(cls)}
        clean = {k: v for k, v in data.items() if k in known}
        try:
            obj = cls(**clean)
        except Exception:
            obj = cls()
        obj._sanitise()
        return obj

    def _sanitise(self) -> None:
        if self.theme not in ("dark", "light"):
            self.theme = "dark"
        self.font_size = max(11, min(26, int(self.font_size or 15)))
        self.daily_session_length = max(5, min(120, int(self.daily_session_length or 20)))
        self.window_w = max(900, int(self.window_w or 1280))
        self.window_h = max(620, int(self.window_h or 820))
        for key in ("vsplit", "hsplit"):
            val = getattr(self, key)
            if not isinstance(val, list) or not all(isinstance(x, int) for x in val):
                setattr(self, key, list(DEFAULTS[key]))

    def save(self, path: Path | None = None) -> None:
        path = path or SETTINGS_PATH
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            # Never let a failed settings write stop someone from learning.
            pass
