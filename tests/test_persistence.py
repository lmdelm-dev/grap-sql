"""Settings persistence and resilience."""
from __future__ import annotations

import json
from pathlib import Path

from sqlschool.config import Settings


def test_round_trip(school_dir):
    path = school_dir / "settings.json"
    s = Settings(theme="light", font_size=18, type_along=False,
                 reduce_motion=True, pro_mode=True, learner_name="Ada")
    s.save(path)
    loaded = Settings.load(path)
    assert loaded.theme == "light"
    assert loaded.font_size == 18
    assert loaded.type_along is False
    assert loaded.reduce_motion is True
    assert loaded.pro_mode is True
    assert loaded.learner_name == "Ada"


def test_missing_file_gives_defaults(school_dir):
    s = Settings.load(school_dir / "nope.json")
    assert s.theme == "dark"
    assert s.font_size == 15
    assert s.onboarded is False


def test_corrupted_file_falls_back(school_dir):
    path = school_dir / "settings.json"
    path.write_text("{not json at all", encoding="utf-8")
    s = Settings.load(path)
    assert s.theme == "dark"


def test_bad_values_are_sanitised(school_dir):
    path = school_dir / "settings.json"
    path.write_text(json.dumps(
        {"theme": "neon", "font_size": 500, "window_h": 1,
         "vsplit": "oops"}), encoding="utf-8")
    s = Settings.load(path)
    assert s.theme == "dark"
    assert 11 <= s.font_size <= 26
    assert s.window_h >= 620
    assert isinstance(s.vsplit, list) and len(s.vsplit) == 2


def test_save_is_atomic(school_dir):
    path = school_dir / "settings.json"
    Settings(theme="dark").save(path)
    tmp = school_dir / "settings.tmp"
    assert not tmp.exists()  # temporary file was moved into place


def test_progress_store_recovers_when_connect_fails(school_dir, monkeypatch):
    import sqlite3

    from sqlschool.memory import store as store_mod
    from sqlschool.memory.store import ProgressStore

    db = school_dir / "progress.db"
    db.write_bytes(b"this is not a database")
    real_connect = sqlite3.connect
    calls = {"n": 0}

    def flaky_connect(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise sqlite3.DatabaseError("simulated unreadable database")
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(store_mod.sqlite3, "connect", flaky_connect)
    st = ProgressStore(path=db)  # must not raise
    assert st.learner_name() == ""
    st.close()
    assert list(school_dir.glob("progress-corrupt-*.db"))