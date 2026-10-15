"""UI smoke tests (offscreen): the window builds, runs real queries,
drives the 3 panes, gates the Next button, and grades answers."""
from __future__ import annotations

import pytest

pytest.importorskip("pytestqt")


@pytest.fixture()
def window(qtbot, school_dir):
    from sqlschool.app import make_window
    from sqlschool.config import Settings

    s = Settings.load()
    s.onboarded = True          # skip the welcome dialog in tests
    s.type_along = True
    s.reduce_motion = True      # deterministic asserts
    win = make_window(s)
    win.show()
    qtbot.addWidget(win)
    return win


def test_window_has_three_panes(window):
    from sqlschool import APP_NAME
    from sqlschool.ui.teacher import TeacherPane
    from sqlschool.ui.output import OutputPane

    assert window.windowTitle() == APP_NAME
    assert isinstance(window.teacher, TeacherPane)
    assert isinstance(window.output, OutputPane)
    assert window.lesson_lbl.text()  # current lesson shown in the top bar


def test_first_step_is_l01_answer_activity(window, qtbot):
    assert window.session.step.id == "L01-1"
    assert window.session.step.kind == "answer"
    assert window.editor.ghost_sql == ""


def test_demo_step_runs_and_fills_output(window, qtbot):
    window.jump_to("L01", "L01-2")
    assert "products" in (window.editor.ghost_sql or "")
    window.editor.setPlainText("SELECT * FROM products;")
    qtbot.mouseClick(window.run_btn, __import__("PySide6").QtCore.Qt.MouseButton.LeftButton)
    qtbot.wait(50)
    assert window.passed_this_step
    assert window.output.result.rowCount() == 40


def test_wrong_query_does_not_pass(window, qtbot):
    window.jump_to("L04", "L04-1")
    window.editor.setPlainText("SELECT name FROM products WHERE price > 99999;")
    window.run_query()
    qtbot.wait(50)
    assert not window.passed_this_step
    assert window.next_btn.isEnabled() is False


def test_next_button_gated_then_advances(window, qtbot):
    window.jump_to("L04", "L04-1")
    window.run_query()                    # fails: no SQL typed
    qtbot.wait(30)
    assert not window.passed_this_step
    window.editor.setPlainText("SELECT name FROM products WHERE price > 100;")
    window.run_query()
    qtbot.wait(30)
    assert window.passed_this_step
    assert window.next_btn.isEnabled()
    window._next_step()
    assert window.session.step.id == "L04-2"


def test_predict_step_graded_as_text_answer(window, qtbot):
    window.jump_to("L04", "L04-5")
    window.editor.setPlainText("21")
    window.run_query()
    qtbot.wait(30)
    assert window.passed_this_step


def test_hint_button_appends_output(window, qtbot):
    window.jump_to("L05", "L05-1")
    text_before = window.output.messages.toPlainText()
    window.show_hint()
    qtbot.wait(30)
    assert window.output.messages.toPlainText() != text_before
    assert window.session.hints_shown == 1


def test_reset_restores_shop(window, qtbot):
    window.sandbox.run("DELETE FROM products;")
    assert window.sandbox.scalar("SELECT count(*) FROM products") == 0
    window.reset_shop()
    assert window.sandbox.scalar("SELECT count(*) FROM products") == 40


def test_completed_lesson_advances_to_next(window, qtbot):
    # skip to the final step of L01 and pass it
    less = window.current_lesson()
    last = len(less.steps) - 1
    window.jump_to("L01", less.steps[last].id)
    window.passed_this_step = True
    window._next_step()
    assert window.lesson_index == 1  # moved on to L02


def test_paste_button_visibility_matches_mode(window):
    window.jump_to("L04", "L04-1")     # type step: SQL entry
    assert not window.paste_btn.isHidden()
    window.jump_to("L01", "L01-1")     # answer step: nothing to paste
    assert window.paste_btn.isHidden()


def test_slow_down_button_reaches_controller(window, qtbot):
    from PySide6.QtCore import Qt

    before = window.output.messages.toPlainText()
    qtbot.mouseClick(window.teacher.slow_button, Qt.MouseButton.LeftButton)
    qtbot.wait(30)
    assert window.output.messages.toPlainText() != before
    assert "Slowing down" in window.output.messages.toPlainText()