"""Turn raw SQLite error messages into warm, plain-English help.

A mistake is never *wrong* here - it is always "almost!".  These translations
are deliberately human.  When a message mentions a table or column name that
is close to something real in the shop, we suggest the correct spelling.
"""
from __future__ import annotations

import re

_NO_SUCH_TABLE = re.compile(r"no such table: (\S+)", re.IGNORECASE)
_NO_SUCH_COLUMN = re.compile(r"no such column: ([^\s(]+)", re.IGNORECASE)
_NO_SUCH_FUNCTION = re.compile(r"no such function: (\S+)", re.IGNORECASE)
_NO_SUCH_INDEX = re.compile(r"no such index: (\S+)", re.IGNORECASE)
_NEAR = re.compile(r'near "([^"]*)": syntax error', re.IGNORECASE)
_NEAR_TOK = re.compile(r'unknown token: ?"?([^"]*)"?', re.IGNORECASE)
_INCOMPLETE = re.compile(r"incomplete input", re.IGNORECASE)
_UNCLOSED = re.compile(r"unterminated string", re.IGNORECASE)
_UNIQUE = re.compile(r"UNIQUE constraint failed: ([^,]+)", re.IGNORECASE)
_NOTNULL = re.compile(r"NOT NULL constraint failed: ([^,]+)", re.IGNORECASE)
_CHECK = re.compile(r"CHECK constraint failed", re.IGNORECASE)
_FK = re.compile(r"FOREIGN KEY constraint failed", re.IGNORECASE)
_DATATYPE = re.compile(r"datatype mismatch", re.IGNORECASE)
_AMBIGUOUS = re.compile(r"ambiguous column name: ([^\s(]+)", re.IGNORECASE)
_MISUSE = re.compile(r"misuse of aggregate (function )?([^\s(]+)", re.IGNORECASE)
_GROUPBY = re.compile(r"GROUP BY clause error", re.IGNORECASE)
_MULTIPLE = re.compile(r"multiple statements in a single prepare", re.IGNORECASE)
_TB_FULL = re.compile(r"table ([^\s]+) may not be modified|readonly", re.IGNORECASE)
_COL_AMBIG_SHORT = re.compile(r"ambiguous column name", re.IGNORECASE)


def levenshtein(a: str, b: str, cap: int = 4) -> int:
    """Small edit distance, capped - good enough for "did you mean?"."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    a, b = a.lower(), b.lower()
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
        if min(prev) > cap:
            return cap + 1
    return prev[-1]


def suggest(word: str, candidates: list[str]) -> str | None:
    word = word.strip().strip('"').strip("`").strip("'")
    if not word or not candidates:
        return None
    best, best_dist = None, 3
    for cand in candidates:
        d = levenshtein(word, cand)
        if d < best_dist:
            best, best_dist = cand, d
    return best


def friendly_error(msg: str, tables: list[str] | None = None,
                   columns: list[str] | None = None) -> str:
    """Translate one SQLite error message (may take schema names for hints)."""
    msg = str(msg or "")
    low = msg.lower()

    if "interrupted" in low:
        return (
            "That query was taking a long time, so I paused it to keep things "
            "snappy. Try a LIMIT or a smaller range."
        )

    m = _UNIQUE.search(msg)
    if m:
        return (
            "This row is trying to reuse a value that has to stay unique "
            "(think of it like a phone number - nobody else can have yours). "
            "Change the value and try again."
        )
    m = _NOTNULL.search(msg)
    if m:
        col = m.group(1)
        return (
            "Every row needs a value in the %s column, and this one is empty. "
            "Give it a value and try again." % col
        )
    m = _FK.search(msg)
    if m:
        return (
            "This row points to a row in another table that isn't there. "
            "Like referencing an order from a customer that doesn't exist - "
            "check the ID you used."
        )
    m = _CHECK.search(msg)
    if m:
        return (
            "The shop has a rule for this column (for example 'price must be "
            "at least 0') and this row breaks it. Check the rule for that "
            "column and adjust your value."
        )
    m = _DATATYPE.search(msg)
    if m:
        return (
            "The types don't match - for example comparing a number to text. "
            "Numbers need numbers, text needs quotes like 'Marrakech'."
        )
    m = _INCOMPLETE.search(msg)
    if m:
        return "The query looks cut off. Did you leave a semicolon or a closing bracket off?"
    m = _UNCLOSED.search(msg)
    if m:
        return (
            "A text value was never closed. Every piece of text starts and "
            "ends with a quote, like 'Marrakech' - check you have both."
        )

    m = _NO_SUCH_TABLE.search(msg)
    if m:
        name = m.group(1)
        hint = suggest(name, tables or [])
        base = "I couldn't find a table called %s." % name
        if hint:
            base += " Did you mean %s?" % hint
        base += " You can check the table names in the Schema browser."
        return base

    m = _NO_SUCH_COLUMN.search(msg)
    if m:
        name = m.group(1)
        hint = suggest(name, columns or [])
        base = "I couldn't find a column called %s." % name
        if hint:
            base += " Did you mean %s?" % hint
        return base

    m = _NO_SUCH_FUNCTION.search(msg)
    if m:
        name = m.group(1)
        hint = suggest(name, ["count", "sum", "avg", "max", "min", "round", "upper", "lower"])
        base = "I don't know a function called %s." % name
        if hint:
            base += " Did you mean %s?" % hint
        return base

    m = _NO_SUCH_INDEX.search(msg)
    if m:
        return "I couldn't find that index. Indexes are like the index at the back of a book - we don't have one with that name yet."

    m = _AMBIGUOUS.search(msg)
    if m:
        return (
            "Both tables have a column called %s, so I can't tell which one "
            "you mean. Be specific and write products.name (table name, "
            "then a dot, then the column)." % m.group(1)
        )

    m = _MISUSE.search(msg)
    if m:
        return (
            "COUNT, SUM, AVG and friends are grand totals - they swallow whole "
            "columns. You can't mix them with ordinary per-row columns; either "
            "drop one of them, or add a GROUP BY so they group together."
        )

    m = _GROUPBY.search(msg)
    if m:
        return (
            "Every column in your SELECT needs to be accounted for: either it "
            "appears in GROUP BY, or it's wrapped in COUNT/SUM/AVG. Pick one."
        )

    m = _MULTIPLE.search(msg)
    if m:
        return (
            "That prepared the same query twice, which isn't needed. You can "
            "just run it once."
        )

    m = _NEAR.search(msg) or _NEAR_TOK.search(msg)
    if m:
        token = m.group(1)
        if token and token.strip().lower() in ("select", "from", "where", "group", "order", "having", "limit", "join", "on", "by"):
            return (
                "I stopped near the word %r - it looks like it's in the wrong "
                "spot. The recipe for a query is: SELECT … FROM … WHERE … "
                "ORDER BY … LIMIT …" % token
            )
        return (
            "I stopped near %r - a spelling slipped in, or a comma is missing. "
            "Check the words between the last working keyword and here." % token
        )

    if "syntax error" in low:
        return (
            "The grammar needs a small fix - often a missing comma, a space "
            "between words, or an extra symbol. Look just before the message "
            "and tidy that spot."
        )

    if "no query solution" in low:
        return "I couldn't match that statement to anything. Try SELECT, INSERT, UPDATE or DELETE."

    if re.search(r"can't open|unable to open", low):
        return "I tried to open a file, and the sandbox stopped me - we stay inside the practice shop here."

    if re.search(r"file is not a database|not a database", low):
        return "That doesn't look like a database to my practice copy."

    if "authorizer" in low:
        return "The sandbox stopped that one - it could touch things outside our practice shop."

    if "table .* may not be modified" in low or "readonly" in low:
        return "That table is read-only in this practice shop, so we won't modify it."

    if "no such table" in low and ":" in msg and len(msg) < 60:
        return "I couldn't find that table - check the name against the Schema browser."

    # Last resort: keep the original but explain what happened.
    return ("The database said: %s. That usually means a small spelling or "
            "punctuation detail - read it slowly and try again." % msg)