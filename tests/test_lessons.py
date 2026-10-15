"""Lesson data integrity: every shipped lesson is valid and self-consistent."""
from __future__ import annotations

from sqlschool.lessons.loader import load_lessons
from sqlschool.lessons.model import validate_step


def test_all_lessons_load():
    lessons, problems = load_lessons()
    assert not problems, problems
    assert len(lessons) >= 8           # release gate: first 8 lessons definitely there
    assert sum(len(l.steps) for l in lessons) >= 60   # …with 60+ exercises


def test_every_step_valid():
    lessons, _ = load_lessons()
    bad = []
    for lesson in lessons:
        for step in lesson.steps:
            for p in validate_step(step, lesson.id):
                bad.append(p)
    assert not bad, bad[:10]


def test_graded_reference_solutions_all_pass(school_dir):
    """The real gate: run every reference solution through the grader."""
    from sqlschool.db.sandbox import Sandbox
    from sqlschool.engine.session import LessonSession
    from sqlschool.memory.store import ProgressStore

    lessons, _ = load_lessons()
    store = ProgressStore()
    failures = []
    for lesson in lessons:
        sb = Sandbox()
        ses = LessonSession(lesson, sb, store)
        for i, step in enumerate(lesson.steps):
            ses.load_step(i)
            ref = step.reference_solution()
            if not ref:
                continue
            out = ses.run(ref)
            if not out.passed:
                failures.append("%s/%s: %s" % (lesson.id, step.id, out.verdict.detail[:80]))
        sb.close()
    assert not failures, failures[:10]


def test_step_ids_match_lesson(lessons):
    for lesson in lessons:
        for step in lesson.steps:
            assert step.id.startswith(lesson.id + "-") or step.id.startswith(lesson.id[0:2][:2].upper() + "-")


def test_titles_and_prompts_not_empty(lessons):
    for lesson in lessons:
        assert lesson.title.strip()
        assert lesson.order >= 1
        for step in lesson.steps:
            assert step.prompt.strip()