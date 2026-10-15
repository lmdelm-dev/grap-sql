"""Fast, simple search across every loaded exercise.

With thousands of generated drills, people need to *find* the one they mean.
The search is a plain substring scan over the words a learner can see (lesson
title, step title, prompt, task, tags and even the reference SQL).  It is
deliberately simple and allocation-light so it stays instant on 10k+ steps.
"""
from __future__ import annotations


def _haystack(lesson, step) -> str:
    parts = [
        lesson.title,
        " ".join(lesson.concept_tags or []),
        step.title,
        step.prompt,
        step.task,
        step.expected_sql,
    ]
    return " ".join(p for p in parts if p).lower()


def search(lessons, query: str, limit: int = 200) -> list[tuple]:
    """Return (lesson, step) pairs whose text contains *query*.

    An empty query returns nothing (so the UI can show a gentle prompt).
    """
    q = (query or "").strip().lower()
    if not q:
        return []
    terms = q.split()
    out: list[tuple] = []
    for lesson in lessons:
        for step in lesson.steps:
            hay = _haystack(lesson, step)
            if all(t in hay for t in terms):
                out.append((lesson, step))
                if len(out) >= limit:
                    return out
    return out


def tags(lessons) -> dict[str, int]:
    """Count how many lessons carry each concept tag."""
    counts: dict[str, int] = {}
    for lesson in lessons:
        for tag in lesson.concept_tags or []:
            counts[tag] = counts.get(tag, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


__all__ = ["search", "tags"]
