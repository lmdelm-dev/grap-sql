"""Achievements: small badges that celebrate real progress.

Each achievement is a tiny rule over a plain stats dictionary produced by
:meth:`ProgressStore.stats`.  Keeping the rules data-driven means new badges
can be added without touching any UI - the Achievements dialog simply lists
whatever this module knows about.
"""
from __future__ import annotations


def _stat(stats, key):
    try:
        return stats.get(key, 0) or 0
    except Exception:
        return 0


ACHIEVEMENTS = [
    {
        "id": "first_steps",
        "title": "First steps",
        "emoji": "🌱",
        "hint": "Finish your very first exercise.",
        "test": lambda s: _stat(s, "passed") >= 1,
    },
    {
        "id": "ten_clean",
        "title": "Getting the hang of it",
        "emoji": "🔟",
        "hint": "Pass 10 exercises.",
        "test": lambda s: _stat(s, "passed") >= 10,
    },
    {
        "id": "fifty_clean",
        "title": "Fifty club",
        "emoji": "🏅",
        "hint": "Pass 50 exercises.",
        "test": lambda s: _stat(s, "passed") >= 50,
    },
    {
        "id": "hundred_clean",
        "title": "Century",
        "emoji": "💯",
        "hint": "Pass 100 exercises.",
        "test": lambda s: _stat(s, "passed") >= 100,
    },
    {
        "id": "no_hints",
        "title": "Flying solo",
        "emoji": "🕊️",
        "hint": "Pass 10 exercises with no hints at all.",
        "test": lambda s: _stat(s, "perfect") >= 10,
    },
    {
        "id": "first_mastery",
        "title": "Mastered one",
        "emoji": "⭐",
        "hint": "Get one exercise to Mastered.",
        "test": lambda s: _stat(s, "mastered") >= 1,
    },
    {
        "id": "twenty_mastered",
        "title": "Memory maker",
        "emoji": "🧠",
        "hint": "Reach 20 mastered exercises.",
        "test": lambda s: _stat(s, "mastered") >= 20,
    },
    {
        "id": "streak_3",
        "title": "Three in a row",
        "emoji": "🔥",
        "hint": "Practise on 3 days in a row.",
        "test": lambda s: _stat(s, "streak_best") >= 3,
    },
    {
        "id": "streak_7",
        "title": "A whole week",
        "emoji": "📅",
        "hint": "Practise on 7 days in a row.",
        "test": lambda s: _stat(s, "streak_best") >= 7,
    },
    {
        "id": "explorer",
        "title": "Explorer",
        "emoji": "🧭",
        "hint": "Try exercises from 5 different lessons.",
        "test": lambda s: _stat(s, "lessons_touched") >= 5,
    },
    {
        "id": "reviewer",
        "title": "Reviewer",
        "emoji": "🔁",
        "hint": "Complete 10 exercises that were due for review.",
        "test": lambda s: _stat(s, "reviews_done") >= 10,
    },
    {
        "id": "level_5",
        "title": "Rising star",
        "emoji": "🌟",
        "hint": "Reach level 5.",
        "test": lambda s: _stat(s, "level") >= 5,
    },
    {
        "id": "level_10",
        "title": "SQL scholar",
        "emoji": "🎓",
        "hint": "Reach level 10.",
        "test": lambda s: _stat(s, "level") >= 10,
    },
    {
        "id": "comeback",
        "title": "Comeback kid",
        "emoji": "💪",
        "hint": "Pass 25 exercises after fixing earlier mistakes.",
        "test": lambda s: _stat(s, "passed") >= 25 and _stat(s, "mistakes") >= 1,
    },
]

_BY_ID = {a["id"]: a for a in ACHIEVEMENTS}


def evaluate(stats: dict) -> set[str]:
    """Return the ids of every achievement the stats satisfy."""
    earned = set()
    for a in ACHIEVEMENTS:
        try:
            if a["test"](stats):
                earned.add(a["id"])
        except Exception:
            continue
    return earned


def describe(achievement_id: str) -> dict:
    return _BY_ID.get(achievement_id, {
        "id": achievement_id, "title": achievement_id, "emoji": "🏆",
        "hint": "",
    })


__all__ = ["ACHIEVEMENTS", "evaluate", "describe"]
