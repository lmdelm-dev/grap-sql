"""The practice database (a friendly Moroccan shop).

Every exercise gets a *fresh* copy of this database, loaded straight into
memory, so a learner can never permanently damage anything.  Pressing Reset
simply reloads the original bytes.
"""
from __future__ import annotations

import sqlite3
from functools import lru_cache
from pathlib import Path

from ..paths import practice_db_path


class PracticeDataMissing(RuntimeError):
    """Raised when the bundled practice database cannot be found."""


@lru_cache(maxsize=1)
def pristine_bytes() -> bytes:
    path = practice_db_path()
    if not path.exists():
        raise PracticeDataMissing(
            "I couldn't find the practice shop database at:\n  %s\n"
            "Please make sure the 'data' folder came with the app." % path
        )
    return path.read_bytes()


def new_connection() -> sqlite3.Connection:
    """A brand-new in-memory copy of the pristine shop database."""
    conn = sqlite3.connect(":memory:")
    conn.deserialize(pristine_bytes())
    return conn


def reset_connection(conn: sqlite3.Connection) -> sqlite3.Connection:
    """Throw away every change and reload the original shop."""
    try:
        conn.close()
    except Exception:
        pass
    return new_connection()


def table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [r[0] for r in rows]


def schema_info(conn: sqlite3.Connection) -> list[dict]:
    """Describe every table, for the schema browser."""
    out = []
    for name in table_names(conn):
        cols = []
        for cid, cname, ctype, notnull, dflt, pk in conn.execute(
            'PRAGMA table_info("%s")' % name
        ):
            cols.append(
                {
                    "name": cname,
                    "type": ctype or "",
                    "pk": bool(pk),
                    "notnull": bool(notnull),
                }
            )
        fks = []
        for row in conn.execute('PRAGMA foreign_key_list("%s")' % name):
            # id, seq, table, from, to, on_update, on_delete, match
            fks.append({"from": row[3], "table": row[2], "to": row[4]})
        count = conn.execute('SELECT COUNT(*) FROM "%s"' % name).fetchone()[0]
        out.append({"name": name, "columns": cols, "foreign_keys": fks, "rows": count})
    return out


def snapshot_state(conn: sqlite3.Connection) -> dict:
    """A canonical picture of every row in the database.

    Used to grade INSERT / UPDATE / DELETE, where two different queries can
    be equally correct as long as the *database ends up the same*.  Row order
    does not matter here, so each table's rows are sorted into a stable form.
    """
    state: dict[str, tuple] = {}
    for name in table_names(conn):
        rows = conn.execute('SELECT * FROM "%s"' % name).fetchall()
        normalised = sorted(repr(tuple(r)) for r in rows)
        state[name] = tuple(normalised)
    return state


def state_diff(before: dict, after: dict) -> dict:
    """Which tables changed between two snapshots, and by how much."""
    diff = {}
    for name in set(before) | set(after):
        b = list(before.get(name, ()))
        a = list(after.get(name, ()))
        if b != a:
            diff[name] = {"before": len(b), "after": len(a)}
    return diff
