"""The safe, sandboxed SQL runner.

Everything the learner types goes through :class:`Sandbox`.  It is built to
answer a query without ever being able to freeze the app or touch the real
computer:

* it runs on a **throw-away in-memory copy** of the shop;
* ``ATTACH`` / ``DETACH`` (reaching other files) and extension loading are
  refused by a SQLite authoriser;
* a **time budget** aborts runaway queries;
* a **row cap** stops a ``SELECT`` from returning a million rows;
* the result is returned as plain data (columns + rows), never as a live
  connection the UI might keep using.
"""
from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass, field

from . import practice

# How much of a result we ever hold in memory / draw.
ROW_CAP = 1000
# Longest we let a single query run before we politely stop it.
DEFAULT_TIME_MS = 2000

# Authoriser action codes (guarded with getattr for older Pythons).
SQLITE_DENY = getattr(sqlite3, "SQLITE_DENY", 1)
SQLITE_ATTACH = getattr(sqlite3, "SQLITE_ATTACH", 24)
SQLITE_DETACH = getattr(sqlite3, "SQLITE_DETACH", 25)
SQLITE_PRAGMA = getattr(sqlite3, "SQLITE_PRAGMA", 19)
SQLITE_FUNCTION = getattr(sqlite3, "SQLITE_FUNCTION", 31)

# PRAGMAs that only *read* how the database is built - safe and useful.
SAFE_PRAGMAS = {
    "table_info",
    "table_xinfo",
    "table_list",
    "index_list",
    "index_info",
    "foreign_key_list",
    "database_list",
    "encoding",
    "page_count",
    "user_version",
}

BANNED_FUNCTIONS = {"load_extension"}

MODIFY_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "create",
    "drop",
    "alter",
    "replace",
    "vacuum",
    "reindex",
}


@dataclass
class QueryResult:
    ok: bool
    sql: str
    columns: list[str] = field(default_factory=list)
    rows: list[tuple] = field(default_factory=list)
    rowcount: int = 0
    truncated: bool = False
    kind: str = "select"          # "select" | "modify"
    message: str = ""
    error: str | None = None      # raw sqlite message
    changes: int = 0
    elapsed_ms: float = 0.0
    state: dict | None = None     # database snapshot after a change
    statements: int = 1

    @property
    def returned_rows(self) -> bool:
        return bool(self.columns)


def _split_statements(sql: str) -> list[str]:
    """Split on semicolons that sit outside quotes/brackets/strings."""
    statements: list[str] = []
    buf = []
    in_squote = in_dquote = False
    in_line_comment = False
    depth = 0
    i = 0
    while i < len(sql):
        ch = sql[i]
        nxt = sql[i + 1] if i + 1 < len(sql) else ""
        if in_line_comment:
            buf.append(ch)
            if ch == "\n":
                in_line_comment = False
            i += 1
            continue
        if not in_squote and not in_dquote:
            if ch == "-" and nxt == "-":
                in_line_comment = True
                buf.append(ch); buf.append(nxt)
                i += 2
                continue
            if ch == "/" and nxt == "*":          # block comment runs to */
                end = sql.find("*/", i + 2)
                if end == -1:
                    buf.append(sql[i:])
                    break
                buf.append(sql[i : end + 2])
                i = end + 2
                continue
        if in_squote:
            buf.append(ch)
            if ch == "'":
                if nxt == "'":          # '' escaped quote inside a string
                    buf.append(nxt)
                    i += 2
                    continue
                in_squote = False
            i += 1
            continue
        if in_dquote:
            buf.append(ch)
            if ch == '"':
                in_dquote = False
            i += 1
            continue
        if ch == "'":
            in_squote = True
            buf.append(ch)
        elif ch == '"':
            in_dquote = True
            buf.append(ch)
        elif ch == "(":
            depth += 1
            buf.append(ch)
        elif ch == ")":
            depth = max(0, depth - 1)
            buf.append(ch)
        elif ch == ";" and depth == 0:
            text = "".join(buf).strip()
            if text:
                statements.append(text)
            buf = []
        else:
            buf.append(ch)
        i += 1
    text = "".join(buf).strip()
    if text:
        statements.append(text)
    return statements


def _make_authorizer(denied: list[str]):
    def authorizer(action, arg1, arg2, dbname, source):  # noqa: ANN001
        if action in (SQLITE_ATTACH, SQLITE_DETACH):
            denied.append(
                "I can't open other files from here - let's stay in our practice shop."
            )
            return SQLITE_DENY
        if action == SQLITE_PRAGMA:
            name = (arg1 or "").lower()
            if name not in SAFE_PRAGMAS:
                denied.append(
                    "That PRAGMA could change how the database runs, so I've "
                    "kept it out of the practice sandbox."
                )
                return SQLITE_DENY
        if action == SQLITE_FUNCTION and (arg2 or "").lower() in BANNED_FUNCTIONS:
            denied.append("That function isn't allowed in the practice sandbox.")
            return SQLITE_DENY
        return 0  # SQLITE_OK

    return authorizer


class Sandbox:
    """Runs SQL safely. One instance owns one in-memory shop copy."""

    def __init__(self, time_ms: int = DEFAULT_TIME_MS, row_cap: int = ROW_CAP):
        self.time_ms = time_ms
        self.row_cap = row_cap
        self.denied: list[str] = []
        self._deadline: float = 0.0
        self.conn = practice.new_connection()
        self._install_guards()
        self.schema = practice.schema_info(self.conn)

    # -- setup ---------------------------------------------------------
    def _install_guards(self) -> None:
        self.denied.clear()
        self.conn.set_authorizer(_make_authorizer(self.denied))
        self.conn.set_progress_handler(self._deadline_check, 1000)

    def _deadline_check(self) -> int:
        if self._deadline and time.monotonic() > self._deadline:
            return 1
        return 0

    # -- housekeeping --------------------------------------------------
    def reset(self) -> None:
        self.conn = practice.reset_connection(self.conn)
        self._deadline = 0.0
        self._install_guards()
        self.schema = practice.schema_info(self.conn)

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    # -- running -------------------------------------------------------
    def run(self, sql: str) -> QueryResult:
        started = time.monotonic()
        result = QueryResult(ok=False, sql=sql)
        self.denied.clear()

        if not sql or not sql.strip():
            result.error = "empty"
            result.message = "There's nothing to run yet - try typing a query first."
            return result

        try:
            statements = _split_statements(sql)
        except Exception as exc:  # very unusual, but never crash the UI
            result.error = "split"
            result.message = str(exc)
            return result

        if not statements:
            result.error = "empty"
            result.message = "There's nothing to run yet - try typing a query first."
            return result

        result.statements = len(statements)
        touches_data = any(_is_modify(s) for s in statements)
        before = practice.snapshot_state(self.conn) if touches_data else None

        self._deadline = time.monotonic() + self.time_ms / 1000.0
        try:
            last_cursor = None
            for stmt in statements:
                last_cursor = self.conn.execute(stmt)
            assert last_cursor is not None

            if last_cursor.description is not None:
                columns = [d[0] for d in last_cursor.description]
                fetched = last_cursor.fetchmany(self.row_cap + 1)
                truncated = len(fetched) > self.row_cap
                rows = [tuple(r) for r in fetched[: self.row_cap]]
                result.ok = True
                result.kind = "select"
                result.columns = columns
                result.rows = rows
                result.rowcount = len(rows)
                result.truncated = truncated
                result.message = "%d row%s" % (len(rows), "" if len(rows) == 1 else "s")
            else:
                result.ok = True
                result.kind = "modify"
                result.rowcount = last_cursor.rowcount if last_cursor.rowcount is not None else 0
                result.changes = self.conn.total_changes
                result.message = _modify_message(statements[-1], result.rowcount)
                if touches_data:
                    self.conn.commit()
                    result.state = practice.snapshot_state(self.conn)

            wiped = practice.snapshot_state(self.conn) if touches_data else None
            if before is not None and wiped is not None and result.state is None:
                result.state = wiped
        except sqlite3.OperationalError as exc:
            msg = str(exc).lower()
            if "interrupted" in msg:
                result.error = "timeout"
                result.message = (
                    "That query was taking a long time, so I paused it to keep "
                    "the app snappy. Try adding a LIMIT or a smaller range."
                )
            else:
                result.error = str(exc)
                result.message = _translate_friendly(str(exc), self.schema)
        except sqlite3.DatabaseError as exc:
            result.error = str(exc)
            result.message = _translate_friendly(str(exc), self.schema)
        except sqlite3.Error as exc:
            result.error = str(exc)
            result.message = _translate_friendly(str(exc), self.schema)

        if not result.ok and self.denied:
            result.message = self.denied[-1]

        result.elapsed_ms = (time.monotonic() - started) * 1000.0
        return result

    # -- convenience for tests / features ------------------------------
    def scalar(self, sql: str, params: tuple = ()) -> object:
        """Run one guarded query and return the first column of the first row.

        Used for internal previews and checks, never for learner text.
        """
        try:
            self._deadline = time.monotonic() + self.time_ms / 1000.0
            cur = self.conn.execute(sql, params) if params else self.conn.execute(sql)
            row = cur.fetchone()
            return row[0] if row is not None else None
        except Exception:
            return None


def _is_modify(statement: str) -> bool:
    text = statement.lstrip()
    # skip leading comments
    while text.startswith("--") or text.startswith("/*"):
        if text.startswith("--"):
            nl = text.find("\n")
            if nl == -1:
                return False
            text = text[nl + 1 :].lstrip()
        else:
            end = text.find("*/")
            if end == -1:
                return False
            text = text[end + 2 :].lstrip()
    first = text.split(None, 1)[0].lower().strip("(") if text else ""
    return first in MODIFY_KEYWORDS


def _modify_message(statement: str, count: int) -> str:
    first = statement.lstrip().split(None, 1)[0].lower()
    verb = {
        "insert": "Added",
        "replace": "Added",
        "update": "Updated",
        "delete": "Deleted",
        "create": "Created",
        "drop": "Dropped",
        "alter": "Changed",
    }.get(first, "Done")
    if first in ("create", "drop", "alter"):
        return "%s ✓" % verb
    noun = "row" if count == 1 else "rows"
    return "%s %d %s ✓" % (verb, count, noun)


def _translate_friendly(raw: str, schema: list[dict]) -> str:
    """Translate a raw SQLite error, using schema names for spelling hints."""
    from ..engine.errors import friendly_error

    tables = [t["name"] for t in schema]
    columns = []
    for t in schema:
        for c in t["columns"]:
            columns.append(c["name"])
    return friendly_error(raw, tables=tables, columns=columns)


def _translate(raw: str) -> str:
    """Fallback English for an error. The rich version lives in engine.errors."""
    from ..engine.errors import friendly_error

    return friendly_error(raw)
