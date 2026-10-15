"""Load lessons from the data/lessons folder.

Lessons live in plain JSON files so new lessons can be added without touching
a single line of Python.  A broken file is skipped - never fatal - so one bad
lesson can't stop anyone from learning.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..paths import lessons_dir
from .model import Hint, Lesson, Step, validate_step

STEP_KINDS = {"type", "fill", "fix", "predict", "answer", "build"}


def _hints(raw, step_id: str) -> list[Hint]:
    hints: list[Hint] = []
    raw = raw or []
    for i, text in enumerate(raw[:4], start=1):
        if isinstance(text, str):
            hints.append(Hint(level=i, text=text))
    return hints


def _steps(data: dict, lesson_id: str) -> list[Step]:
    steps = []
    for idx, raw in enumerate(data.get("steps", []), start=1):
        if not isinstance(raw, dict):
            continue
        kind = str(raw.get("type", "type")).lower()
        if kind not in STEP_KINDS:
            continue
        step = Step(
            kind=kind,
            id="%s-%d" % (lesson_id, idx),
            title=raw.get("title", "Step %d" % idx),
            prompt=raw.get("prompt", ""),
            real_life=raw.get("real_life", ""),
            memory_trick=raw.get("memory_trick", ""),
            task=raw.get("task", ""),
            expected_sql=raw.get("expected_sql", ""),
            seed_sql=raw.get("seed_sql", ""),
            ordered=bool(raw.get("ordered", False)),
            check=raw.get("check") or {},
            hints=_hints(raw.get("hints"), "%s-%d" % (lesson_id, idx)),
            extra=raw.get("extra", ""),
        )
        steps.append(step)
    return steps


def load_lesson(path: Path) -> Lesson | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or not data.get("id") or "steps" not in data:
        return None
    lesson = Lesson(
        id=str(data["id"]),
        title=str(data.get("title", "Untitled lesson")),
        order=int(data.get("order", 0)),
        difficulty=int(data.get("difficulty", 1)),
        concept_tags=list(data.get("tags", [])),
        steps=_steps(data, str(data["id"])),
    )
    return lesson if lesson.steps else None


def load_lessons(folder: Path | None = None) -> tuple[list[Lesson], list[str]]:
    """Load every lesson file (sorted). Returns (lessons, skipped-problems).

    A missing folder is fine; the app just shows no lessons.
    """
    folder = folder or lessons_dir()
    lessons: list[Lesson] = []
    problems: list[str] = []
    if not folder.exists():
        return lessons, problems
    for path in sorted(folder.glob("*.json")):
        lesson = load_lesson(path)
        if lesson is None:
            problems.append("Could not read %s - skipped." % path.name)
            continue
        for step in lesson.steps:
            for prob in validate_step(step, lesson.id):
                problems.append(prob)
        lessons.append(lesson)
    lessons.sort(key=lambda l: l.order)
    return lessons, problems


def all_steps(lessons: list[Lesson]) -> list[Step]:
    return [s for l in lessons for s in l.steps]