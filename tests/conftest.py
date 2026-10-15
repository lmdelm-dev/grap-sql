"""Shared pytest fixtures.

Two environment tweaks make the whole suite run headless and isolated:
* QT_QPA_PLATFORM=offscreen  ->  Qt windows render in memory (no monitor)
* SQLSCHOOL_DIR set per test ->  progress/settings never touch the real home
"""
from __future__ import annotations

import os
import tempfile
import shutil

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import sqlschool.config as _cfg  # noqa: E402


@pytest.fixture()
def school_dir(tmp_path):
    """Give each test its own progress folder, restored afterwards."""
    old = os.environ.get("SQLSCHOOL_DIR")
    folder = tmp_path / "school"
    folder.mkdir(parents=True, exist_ok=True)
    os.environ["SQLSCHOOL_DIR"] = str(folder)
    _cfg.SETTINGS_PATH = _cfg.app_dir() / "settings.json"
    yield folder
    if old is None:
        os.environ.pop("SQLSCHOOL_DIR", None)
    else:
        os.environ["SQLSCHOOL_DIR"] = old


@pytest.fixture()
def sandbox():
    from sqlschool.db.sandbox import Sandbox

    sb = Sandbox()
    yield sb
    sb.close()


@pytest.fixture()
def store(school_dir):
    from sqlschool.memory.store import ProgressStore

    st = ProgressStore()
    yield st
    st.close()


@pytest.fixture()
def lessons():
    from sqlschool.lessons.loader import load_lessons

    loaded, problems = load_lessons()
    assert not problems, problems
    return loaded