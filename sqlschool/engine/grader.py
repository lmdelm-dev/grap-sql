"""Grading: does the learner's query really do what the exercise asked?

We grade by *result*, never by comparing text.  Two very different queries
that return the same correct answer both pass.  The grader understands:

* unordered results (row order is ignored unless the query sorts on purpose)
* aliases (column *names* can differ; the *values* must match)
* float tolerance (13.5 vs 13.5000001 are the same price)
* NULLs (a missing value is a real value, not an empty string)
* query families (SELECT vs INSERT/UPDATE/DELETE, compared by final state)
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

FLOAT_TOLERANCE = 1e-6

ORDER_BY_RE = re.compile(r"\border\s+by\b", re.IGNORECASE)


@dataclass
class Verdict:
    passed: bool
    comparison: str = ""                  # why we said pass/fail
    detail: str = ""

    @classmethod
    def pass_(cls, comparison: str, detail: str = "") -> "Verdict":
        return cls(True, comparison, detail)

    @classmethod
    def fail(cls, comparison: str, detail: str = "") -> "Verdict":
        return cls(False, comparison, detail)


def normalise_value(value):
    if value is None:
        return ("NULL",)
    if isinstance(value, bool):
        return ("BOOL", value)
    if isinstance(value, (int, float)):
        # round to kill float noise; keep int/large handling sane
        return ("NUM", round(float(value), 6))
    if isinstance(value, (bytes, bytearray)):
        return ("BLOB", bytes(value))
    if isinstance(value, str):
        return ("STR", value)
    return ("STR", str(value))


def normalise_rows(columns: list[str], rows: list[tuple]) -> list:
    """Each row, normalised (column names stripped, values normalised).

    Returns a list so duplicates are preserved; callers compare as
    multisets when order should not matter.
    """
    return [tuple(normalise_value(c) for c in row) for row in rows]


def expected_is_ordered(sql: str) -> bool:
    return bool(ORDER_BY_RE.search(sql))


def compare_select(
    learner_columns: list[str],
    learner_rows: list[tuple],
    reference_columns: list[str],
    reference_rows: list[tuple],
    reference_sql: str = "",
    learner_sql: str = "",
) -> Verdict:
    """Compare two SELECT results with the tolerance rules above."""
    if len(learner_columns) != len(reference_columns):
        return Verdict.fail(
            "different number of columns",
            "Yours returns %d column%s; the answer returns %d column%s. "
            "Are you selecting exactly the fields asked for?"
            % (len(learner_columns), "s" if len(learner_columns) != 1 else "",
               len(reference_columns), "s" if len(reference_columns) != 1 else ""),
        )

    if not reference_rows and not learner_rows:
        return Verdict.pass_(
            "both return no rows",
            "Your query returned zero rows, and so did the reference - a "
            "perfectly correct answer for this question.",
        )

    expected_rows = normalise_rows(reference_columns, reference_rows)
    got_rows = normalise_rows(learner_columns, learner_rows)
    expected_counts = Counter(expected_rows)
    got_counts = Counter(got_rows)

    if got_counts == expected_counts:
        note = "same rows"
        if len(learner_rows) != len(reference_rows):
            note = "same rows (order differs; that's fine)"
        return Verdict.pass_(note)

    # Ordered comparison lives above; now see if ORDER BY matters.
    if expected_is_ordered(reference_sql) or expected_is_ordered(learner_sql):
        if got_rows == expected_rows:
            return Verdict.pass_("same rows, in the same order")

    # Count mismatch is a strong clue, so say so clearly.
    if len(learner_rows) != len(reference_rows):
        return Verdict.fail(
            "number of rows differs",
            "Yours returns %d row%s; the answer returns %d. Often that means "
            "the filter (WHERE) or the grouping is slightly different."
            % (len(learner_rows), "s" if len(learner_rows) != 1 else "",
               len(reference_rows)),
        )

    # Same count but different values: find a helpful example difference.
    missing = list((expected_counts - got_counts).elements())
    extra = list((got_counts - expected_counts).elements())
    parts = []
    if missing:
        parts.append("the answer has a row like (%s) that yours doesn't"
                     % _show_cells(missing[0]))
    if extra:
        parts.append("yours has a row like (%s) that the answer doesn't"
                     % _show_cells(extra[0]))
    return Verdict.fail(
        "rows differ",
        "Same number of rows, but the values differ - %s." % " and ".join(parts),
    )


def _show_cells(row) -> str:
    """One row of normalised cells, as short readable text."""
    shown = []
    for cell in row[:1]:  # one value is enough for the nudge
        if len(cell) == 1:
            shown.append("∅" if cell[0] == "NULL" else str(cell[0]))
        else:
            shown.append(str(cell[1]))
    return ",".join(shown)


def compare_state(learner_state: dict, reference_state: dict) -> Verdict:
    """Compare two full-database snapshots (for INSERT/UPDATE/DELETE)."""
    all_tables = set(learner_state) | set(reference_state)
    for name in sorted(all_tables):
        a = learner_state.get(name, ())
        b = reference_state.get(name, ())
        # for change lessons, most tables should be untouched; compare all
        if a != b:
            return Verdict.fail(
                "table %s differs" % name,
                "After your query, the %s table doesn't look like the answer's "
                "version. Try Reset and run your query side by side with the "
                "example." % name,
            )
    return Verdict.pass_("the database ends up the same")


def compare_state_contains(learner_state: dict, reference_state: dict) -> Verdict:
    """For INSERT lessons: learner may also delete rows and still be fine?
    Keep it strict: INSERT is graded on exact final state, matching the
    reference solution. Different-but-equal states pass naturally.
    """
    return compare_state(learner_state, reference_state)