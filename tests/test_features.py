"""Advanced features: XP & levels, achievements, adaptive review, weak spots,
search, challenge mode and the new UI dialogs."""
from __future__ import annotations

import pytest

from sqlschool.memory.store import (
    ProgressStore,
    level_info,
    today,
    XP_PASS,
)


# -- XP & levels -----------------------------------------------------------
def test_level_info_curve():
    assert level_info(0)["level"] == 1
    assert level_info(99)["level"] == 1
    assert level_info(100)["level"] == 2          # 100 XP buys level 2
    assert level_info(299)["level"] == 2
    assert level_info(300)["level"] == 3          # +200 more buys level 3
    info = level_info(150)
    assert info["into_level"] == 50
    assert info["span"] == 200
    assert info["next_at"] == 300


def test_xp_awarded_on_pass_and_persisted(store):
    store.record_attempt("L02", "L02-1", passed=True, hints=0, time_s=2.0,
                         independent=True)
    assert store.xp() >= XP_PASS
    store.add_xp(300)
    assert store.level_info()["level"] >= 3


def test_failed_step_comes_back_today(store):
    store.record_attempt("L04", "L04-1", passed=False, hints=0, time_s=1.0)
    row = store.step_row("L04", "L04-1")
    assert row["last_result"] == "fail"
    assert row["due"] == today()            # same-day retry, not tomorrow
    assert any(r["step_id"] == "L04-1" for r in store.due_steps())


def test_weak_spots_lists_trouble_first(store):
    store.record_attempt("L04", "L04-1", passed=False, hints=0, time_s=1.0)
    store.record_attempt("L05", "L05-1", passed=False, hints=0, time_s=1.0)
    store.record_attempt("L04", "L04-1", passed=False, hints=0, time_s=1.0)
    weak = store.weak_spots()
    assert weak
    assert weak[0]["lesson_id"] == "L04"    # most lapses float to the top


def test_achievements_unlock_once(store):
    assert store.check_achievements() == []          # nothing yet
    store.record_attempt("L02", "L02-1", passed=True, hints=0, time_s=1.0,
                         independent=True)
    fresh = store.check_achievements()
    assert "first_steps" in fresh
    assert store.check_achievements() == []          # already remembered


# -- search ----------------------------------------------------------------
def test_search_finds_relevant_steps(lessons):
    from sqlschool.lessons.search import search, tags

    hits = search(lessons, "join", limit=10)
    assert hits
    assert all("join" in (l.title + s.title + s.prompt + s.expected_sql).lower()
               for l, s in hits)
    assert search(lessons, "") == []
    assert tags(lessons)


# -- challenge mode --------------------------------------------------------
def test_challenge_prefers_weak_spots(lessons, store):
    from sqlschool.lessons.challenge import pick_steps

    store.record_attempt("L04", "L04-1", passed=False, hints=0, time_s=1.0)
    steps = pick_steps(lessons, store, count=3, seed=1)
    assert any(s.id == "L04-1" for s in steps)


def test_challenge_builds_lesson(lessons, store):
    from sqlschool.lessons.challenge import make_challenge, CHALLENGE_LESSON_ID

    lesson = make_challenge(lessons, store, count=5, seed=7)
    assert lesson.id == CHALLENGE_LESSON_ID
    assert len(lesson.steps) == 5
    assert all(s.id for s in lesson.steps)


# -- UI --------------------------------------------------------------------
pytest.importorskip("pytestqt")


@pytest.fixture()
def window(qtbot, school_dir):
    from sqlschool.app import make_window
    from sqlschool.config import Settings

    s = Settings.load()
    s.onboarded = True
    s.reduce_motion = True
    s.pro_mode = True
    win = make_window(s)
    win.show()
    qtbot.addWidget(win)
    return win


def test_new_dialogs_build(window):
    from sqlschool.ui import views

    views.SqlReference(window.pal, window)
    views.SchemaBrowser(window.sandbox.schema, window.pal, window)
    views.AchievementsView(window.store, window.pal, window)
    views.WeakSpotsView(window.store, window.pal, window)
    views.SearchDialog(window.lessons, window.pal, window)
    views.ChallengeDialog(window.lessons, window.pal, window)
    views.ProgressView(window.store, window.pal, window)
    views.AboutView(window.pal, window)


def test_dialogs_show_level_and_achievements(window):
    from sqlschool.memory.achievements import ACHIEVEMENTS
    from sqlschool.ui.views import AchievementsView

    window.store.add_xp(300)
    dlg = AchievementsView(window.store, window.pal, window)
    assert dlg.list.count() == len(ACHIEVEMENTS)
    assert window.store.level_info()["level"] >= 3


def test_search_dialog_filters(window):
    from sqlschool.ui.views import SearchDialog

    dlg = SearchDialog(window.lessons, window.pal, window)
    dlg.search.setText("join")
    assert dlg.results.count() > 0


def test_lessons_map_is_lazy(window):
    from sqlschool.ui.views import LessonsMap

    dlg = LessonsMap(window.lessons, window.store, window.pal, window)
    root = dlg.tree.topLevelItem(0)
    # a placeholder child exists, but step rows are only built on expand
    assert root.childCount() == 1
    dlg._on_expanded(root)
    assert root.childCount() == len(window.lessons[0].steps)


def test_challenge_mode_runs_and_finishes(window, qtbot):
    window.start_challenge(3, "", 5)
    assert window.challenge is not None
    assert window.current_lesson().id == "CHALLENGE"
    assert window._challenge_timer is not None
    n = len(window.challenge.steps)
    for _ in range(n):
        window.passed_this_step = True
        window._next_step()
    assert window.challenge is None
    assert window._challenge_timer is None


def test_editor_typing_feedback_selects_typed_text(window):
    ed = window.editor
    ed.set_ghost("SELECT name FROM products;", "type")
    ed.setPlainText("SELECT")
    sels = ed.extraSelections()
    assert len(sels) == 1
    assert sels[0].cursor.selectedText() == "SELECT"
