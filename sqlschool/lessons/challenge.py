"""Challenge mode: build a short, focused quiz out of exercises you know.

A challenge is just a *temporary* lesson assembled on the fly from existing
steps - so the whole lesson engine and grading work unchanged.
We pick the exercises that will help most: weak spots first, then anything
due for review today, then a random spread from the chosen tag.
"""
from __future__ import annotations

import random

from .model import Lesson, Step

CHALLENGE_LESSON_ID = "CHALLENGE"


def _all_steps(lessons) -> list[tuple]:
    return [(lesson, step) for lesson in lessons for step in lesson.steps]


def _find_step(lessons, lesson_id: str, step_id: str):
    for lesson in lessons:
        if lesson.id != lesson_id:
            continue
        for step in lesson.steps:
            if step.id == step_id:
                return lesson, step
    return None


def pick_steps(lessons, store, count: int = 6, tag: str | None = None,
               seed: int | None = None) -> list[Step]:
    """Choose up to *count* steps, best-for-learning first."""
    rng = random.Random(seed) if seed is not None else random.Random()
    chosen: list[Step] = []
    seen: set[str] = set()

    def add(step: Step) -> None:
        if step.id not in seen:
            seen.add(step.id)
            chosen.append(step)

    # 1) weak spots (things that keep going wrong)
    try:
        for row in store.weak_spots(limit=count * 3):
            found = _find_step(lessons, row["lesson_id"], row["step_id"])
            if found and (tag is None or tag in (found[0].concept_tags or [])):
                add(found[1])
            if len(chosen) >= count:
                return chosen[:count]
    except Exception:
        pass

    # 2) anything due for review today
    try:
        for row in store.due_steps():
            found = _find_step(lessons, row["lesson_id"], row["step_id"])
            if found and (tag is None or tag in (found[0].concept_tags or [])):
                add(found[1])
            if len(chosen) >= count:
                return chosen[:count]
    except Exception:
        pass

    # 3) a random spread from the tag (or everywhere)
    pool = _all_steps(lessons)
    if tag:
        pool = [(l, s) for (l, s) in pool if tag in (l.concept_tags or [])]
    rng.shuffle(pool)
    for _lesson, step in pool:
        add(step)
        if len(chosen) >= count:
            break
    return chosen[:count]


def build_lesson(steps: list[Step], title: str = "Challenge",
                 difficulty: int = 3, tags: list[str] | None = None) -> Lesson:
    return Lesson(
        id=CHALLENGE_LESSON_ID,
        title=title,
        order=10 ** 6,
        difficulty=difficulty,
        concept_tags=list(tags or ["challenge"]),
        steps=list(steps),
    )


def make_challenge(lessons, store, count: int = 6, tag: str | None = None,
                   seed: int | None = None) -> Lesson:
    steps = pick_steps(lessons, store, count=count, tag=tag, seed=seed)
    title = "Challenge" + (" · %s" % tag if tag else "")
    return build_lesson(steps, title=title, tags=["challenge"] + ([tag] if tag else []))


__all__ = ["make_challenge", "build_lesson", "pick_steps", "CHALLENGE_LESSON_ID"]
