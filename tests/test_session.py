"""The learner loop: run -> grade -> explain -> record, plus hints."""
from __future__ import annotations

import pytest

from sqlschool.engine.session import LessonSession
from sqlschool.db.sandbox import Sandbox


@pytest.fixture()
def session(school_dir, store):
    from sqlschool.lessons.loader import load_lessons

    lessons, _ = load_lessons()
    lesson = {l.id: l for l in lessons}["L04"]  # WHERE lesson
    sb = Sandbox()
    ses = LessonSession(lesson, sb, store)
    yield ses, sb
    sb.close()


def test_correct_query_passes(session):
    ses, sb = session
    ses.load_step(0)  # L04-1: SELECT name FROM products WHERE price > 100;
    out = ses.run("SELECT name FROM products WHERE price > 100;")
    assert out.passed
    assert out.verdict.passed
    assert out.result.ok
    assert len(out.result.rows) == 21


def test_equivalent_different_query_passes(session):
    ses, sb = session
    ses.load_step(0)
    # same filter written a different but equal way
    out = ses.run("SELECT name FROM products WHERE price >= 100.01;")
    assert out.passed


def test_wrong_rows_fail_kindly(session):
    ses, sb = session
    ses.load_step(0)
    out = ses.run("SELECT name FROM products WHERE price > 500;")
    assert not out.passed
    assert out.teacher_lines  # an explanation was written


def test_broken_sql_fails_with_explanation(session):
    ses, sb = session
    ses.load_step(0)
    out = ses.run("SELECT nmae FROM products;")
    assert not out.passed
    assert any("nmae" in line or "name" in line for line in out.teacher_lines)


def test_predict_step_treated_as_answer(session, store):
    ses, sb = session
    ses.load_step(4)  # L04-5 predict: "how many?" -> "21"
    out = ses.run("21")
    assert out.passed
    assert store.step_row("L04", "L04-5") is not None


def test_hints_progress_1_to_4_then_none(session):
    ses, sb = session
    ses.load_step(0)
    hints = [ses.next_hint() for _ in range(6)]
    assert hints[0] is not None and "hint 1 of 4" in hints[0]
    assert hints[3] is not None and "hint 4 of 4" in hints[3]
    assert hints[4] is None
    assert ses.hints_shown == 4


def test_require_clause_enforcement(school_dir, store):
    from sqlschool.lessons.loader import load_lessons

    lessons, _ = load_lessons()
    lesson = {l.id: l for l in lessons}["L05"]
    sb = Sandbox()
    ses = LessonSession(lesson, sb, store)
    ses.load_step(0)
    # same rows but no ORDER BY -> the step insists
    out = ses.run("SELECT name, price FROM products")
    assert out.result.ok
    assert not out.passed
    assert "order by" in out.verdict.detail.lower()
    out2 = ses.run("SELECT name, price FROM products ORDER BY price;")
    assert out2.passed
    sb.close()


def test_fill_and_fix_prepare_editor(session):
    ses, sb = session
    ses.load_step(1)  # L04-2 fill step has seed SQL
    prep = ses.prepare_editor(ses.step)
    assert prep["mode"] == "fill"
    assert "___" in prep["text"] or prep["text"]


def test_fill_blank_check(session):
    ses, sb = session
    ses.load_step(1)
    out = ses.run(ses.step.seed_sql or "SELECT name FROM products WHERE price ___ 100;")
    assert not out.passed
    assert "blank" in out.teacher_lines[1] or "blank" in " ".join(out.teacher_lines)


def test_demo_step_passes_on_first_run(school_dir, store):
    from sqlschool.lessons.loader import load_lessons

    lessons, _ = load_lessons()
    lesson = {l.id: l for l in lessons}["L01"]
    sb = Sandbox()
    ses = LessonSession(lesson, sb, store)
    ses.load_step(1)  # L01-2 demo: run SELECT * FROM products
    out = ses.run("SELECT * FROM products;")
    assert out.passed
    sb.close()


def test_mistake_notebook_fills_on_failure(school_dir, store):
    from sqlschool.lessons.loader import load_lessons

    lessons, _ = load_lessons()
    lesson = {l.id: l for l in lessons}["L04"]
    sb = Sandbox()
    ses = LessonSession(lesson, sb, store)
    ses.load_step(0)
    ses.run("SELECT name FROM products WHERE price > 99999;")
    mistakes = store.mistakes()
    assert any(m["lesson_id"] == "L04" and m["step_id"] == "L04-1"
               for m in mistakes)
    sb.close()


def test_dml_step_state_graded(school_dir, store):
    from sqlschool.lessons.loader import load_lessons

    lessons, _ = load_lessons()
    lesson = {l.id: l for l in lessons}["L11"]
    sb = Sandbox()
    ses = LessonSession(lesson, sb, store)
    # L11-1 is an INSERT step - find the reference
    step = next(s for s in lesson.steps if s.id == "L11-1")
    ses.load_step(lesson.steps.index(step))
    out = ses.run(step.reference_solution())
    assert out.passed, out.teacher_lines
    sb.close()


def test_fail_explanation_falls_back_to_comparison(session):
    from sqlschool.db.sandbox import QueryResult
    from sqlschool.engine import grader

    ses, sb = session
    step = ses.lesson.steps[0]
    res = QueryResult(ok=True, sql="SELECT name FROM products WHERE price > 500;",
                      columns=["name"], rows=[])
    res.kind = "select"
    verdict = grader.Verdict.fail("number of rows differs")  # detail left empty
    lines = ses._teacher_explanation(step, res.sql, res, verdict)
    assert any("number of rows differs" in line for line in lines)
    assert all(line.strip() != "•" for line in lines)