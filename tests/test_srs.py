"""Spaced repetition (SM-2), streaks, mistakes, backups, export/import."""
from __future__ import annotations

import json
import os
import shutil
import struct
from pathlib import Path

import pytest

from sqlschool.memory.store import (
    ProgressStore,
    _sm2,
    _quality,
    today,
    today_plus,
)


def test_sm2_classic_intervals():
    # quality 5 (clean pass, no hints): 1 -> 3 -> 7 -> 14 days
    reps, ease, interval = _sm2(0, 2.5, 0, 5)
    assert (reps, interval) == (1, 1)
    reps, ease, interval = _sm2(reps, ease, interval, 5)
    assert (reps, interval) == (2, 3)
    reps, ease, interval = _sm2(reps, ease, interval, 5)
    assert (reps, interval) == (3, 7)
    reps, ease, interval = _sm2(reps, ease, interval, 5)
    assert (reps, interval) == (4, 14)


def test_sm2_failure_resets():
    reps, ease, interval = _sm2(4, 2.5, 14, 1)
    assert reps == 0
    assert interval == 1
    assert ease < 2.5


def test_quality_model():
    assert _quality(passed=True, hints=0, time_s=3) == 5
    assert _quality(passed=True, hints=1, time_s=3) == 4
    assert _quality(passed=False, hints=0, time_s=3) == 1
    assert _quality(passed=False, hints=3, time_s=3) == 0


def test_record_attempt_tracks_row(store):
    # first clean passes are independent, so the row becomes "due" (not "new")
    store.record_attempt("L01", "L01-1", passed=True, hints=0, time_s=5.0,
                         independent=True)
    row = store.step_row("L01", "L01-1")
    assert row["attempts"] == 1
    assert row["status"] == "due"
    assert row["due"] == today_plus(1).isoformat()
    assert row["interval_days"] == 1


def test_mastery_needs_repeated_independent_passes(store):
    for _ in range(2):
        store.record_attempt("L02", "L02-1", passed=True, hints=0,
                             time_s=2.0, independent=True)
    row = store.step_row("L02", "L02-1")
    assert row["status"] == "mastered"


def test_flags_with_hints_never_master(store):
    for _ in range(4):
        store.record_attempt("L02", "L02-2", passed=True, hints=1,
                             time_s=2.0, independent=False)
    row = store.step_row("L02", "L02-2")
    # hinted passes don't count as independent, so no mastery
    assert row["status"] != "mastered"


def test_streak_grows_and_respects_gap(store):
    store.on_passed()
    assert store.streak()["current"] == 1
    store.on_passed()
    assert store.streak()["current"] == 1  # same day doesn't double count
    # simulate a gap by rewriting the stored last day
    store._save_streak({"current": 3, "best": 3,
                        "last": (today_plus(-3)).isoformat()})
    store.on_passed()
    assert store.streak()["current"] == 1  # broken chain restarts


def test_mistake_book(store):
    store.add_mistake("L03", "L03-1", "SELECT x", "SELECT y", "why")
    store.add_mistake("L03", "L03-1", "SELECT x2", "SELECT y", "why")
    mistakes = store.mistakes()
    assert len(mistakes) == 1
    assert mistakes[0]["repeat_count"] in (1, 2)
    store.clear_mistake("L03", "L03-1")
    assert store.mistakes() == []


def test_export_import_round_trip(school_dir, store):
    store.record_attempt("L05", "L05-1", passed=True, hints=0, time_s=3.0)
    store.set_learner_name("Ada")
    payload = store.export_json()
    data = json.loads(payload)
    assert data["meta"]["name"] == "Ada"
    assert any(s["step_id"] == "L05-1" for s in data["steps"])

    # fresh store imports the payload
    other_dir = school_dir / "other"
    other = ProgressStore(other_dir / "progress.db")
    counts = other.import_json(payload)
    assert counts["steps"] >= 1
    assert other.step_row("L05", "L05-1") is not None
    other.close()


def test_backup_happens_and_rotates(school_dir, store):
    # the first open creates the db but not a backup yet (nothing to copy)
    store2 = ProgressStore()
    store2.close()
    backups = school_dir / "backups"
    first = sorted(backups.glob("progress-*.db"))
    assert first
    # age the newest backup so the next open makes another
    old = first[-1]
    import datetime as _dt

    t = _dt.datetime.now() - _dt.timedelta(days=2)
    os.utime(old, (t.timestamp(), t.timestamp()))
    store3 = ProgressStore()
    store3.close()
    second = sorted(backups.glob("progress-*.db"))
    assert len(second) == len(first) + 1


def test_corruption_recovery(school_dir):
    bad = school_dir / "progress.db"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"this is not a sqlite file" * 20)
    st = ProgressStore()
    try:
        row = st.conn.execute("SELECT count(*) FROM steps").fetchone()
        assert row[0] == 0
    finally:
        st.close()
    # the broken file was spirited away, not deleted
    assert not bad.exists() or bad.stat().st_size > 0
    leftovers = list((school_dir).glob("progress-corrupt-*.db"))
    assert leftovers


def test_due_steps_uses_schedule(school_dir, store):
    store.record_attempt("L06", "L06-1", passed=True, hints=0, time_s=1.0)
    # its interval schedules it for tomorrow, so simulate the day passing
    store.conn.execute(
        "UPDATE steps SET due=? WHERE lesson_id='L06' AND step_id='L06-1'",
        (today(),))
    store.conn.commit()
    due = store.due_steps()
    assert any(r["step_id"] == "L06-1" for r in due)


def test_progress_summary(school_dir, store):
    store.record_attempt("L01", "L01-1", passed=True, hints=0,
                         time_s=1.0, independent=True)
    store.record_attempt("L01", "L01-2", passed=True, hints=0,
                         time_s=1.0, independent=True)
    s = store.progress_summary([{"id": "a"}, {"id": "b"}, {"id": "c"}])
    assert s["done"] == 2
    assert s["total"] == 3


def test_reset_practice_data(school_dir, store):
    store.record_attempt("L01", "L01-1", passed=True, hints=0, time_s=1.0)
    store.on_passed()
    store.reset_practice_data()
    assert store.step_row("L01", "L01-1") is None or \
        store.step_row("L01", "L01-1")["attempts"] == 0
    assert store.mistakes() == []