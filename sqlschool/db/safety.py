"""Kind, plain-English warnings before a query changes the practice shop.

Nothing is blocked outright - the learner is always allowed to experiment,
because it is only a throw-away copy.  We just say what is about to happen.
"""
from __future__ import annotations

import re

DESTRUCTIVE = re.compile(
    r"^\s*(delete|update|drop|alter|truncate|replace)\b", re.IGNORECASE
)


def destructive_warning(sql: str) -> str | None:
    """Return a friendly heads-up, or None if the query is harmless."""
    text = _strip_comments(sql)
    stripped = text.strip()
    if not stripped:
        return None
    first = stripped.split(None, 1)[0].lower()

    if first in ("drop", "truncate"):
        what = "table" if first == "drop" else "data"
        return (
            "Heads up: this removes a whole %s.\n"
            "That's fine here - it only changes your practice copy, "
            "and Reset puts everything back." % what
        )
    if first == "delete":
        if _has_where(stripped):
            return (
                "Heads up: this deletes some rows.\n"
                "It only changes your practice copy. Reset puts them back."
            )
        return (
            "Heads up: this deletes ALL rows in the table.\n"
            "It only changes your practice copy. Reset puts them back."
        )
    if first == "update":
        if not _has_where(stripped):
            return (
                "Heads up: this changes EVERY row in the table.\n"
                "It only changes your practice copy. Reset puts everything back."
            )
        return (
            "Heads up: this changes some rows.\n"
            "It only changes your practice copy. Reset puts everything back."
        )
    if first == "alter":
        return (
            "Heads up: this changes the shape of a table.\n"
            "It only changes your practice copy. Reset puts everything back."
        )
    return None


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _has_where(stripped: str) -> bool:
    return re.search(r"\bwhere\b", stripped, re.IGNORECASE) is not None


def is_destructive(sql: str) -> bool:
    return DESTRUCTIVE.match(_strip_comments(sql)) is not None
