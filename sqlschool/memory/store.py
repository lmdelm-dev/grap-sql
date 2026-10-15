"""Everything that remembers the learner.

Progress lives in one small SQLite database next to the app settings
(``~/.grap-sql/progress.db``).  It is backed up automatically,
recovered if it is ever corrupted, and can be exported/imported as one JSON
file - so nothing precious is ever lost because of us.
"""
from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import sqlite3
from pathlib import Path

from ..config import app_dir
from . import achievements as _achievements

# How much experience each kind of success is worth.
XP_PASS = 10
XP_INDEPENDENT = 5
XP_MASTERED = 20
XP_FAIL = 2

# Level titles, one per level (the last one repeats for very high levels).
LEVEL_TITLES = [
    "Newcomer", "Curious", "Learner", "Apprentice", "Rising star",
    "Query writer", "Analyst", "Data explorer", "SQL scholar", "Grandmaster",
]


def today() -> str:
    return _dt.date.today().isoformat()


def _from_iso(s: str, default) -> _dt.date:
    if not s:
        return default
    try:
        return _dt.date.fromisoformat(s)
    except Exception:
        return default


class ProgressStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path) if path else (app_dir() / "progress.db")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._recover_if_broken()
        self._backup_if_due()
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self._create_schema()

    # -- lifecycle -----------------------------------------------------
    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    def _recover_if_broken(self) -> None:
        if not self.path.exists():
            return
        broken = False
        try:
            probe = sqlite3.connect(str(self.path))
            try:
                probe.execute("SELECT 1").fetchone()
            finally:
                probe.close()
        except sqlite3.DatabaseError:
            broken = True
        if broken:
            moved = self.path.with_name(
                "progress-corrupt-%s.db" % _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
            )
            try:
                shutil.move(str(self.path), str(moved))
            except Exception:
                pass

    def _backup_if_due(self) -> None:
        backups = self.path.parent / "backups"
        last = None
        if backups.exists():
            files = sorted(backups.glob("progress-*.db"))
            if files:
                last = files[-1]
        if last is None or _dt.datetime.now() - _dt.datetime.fromtimestamp(last.stat().st_mtime) > _dt.timedelta(days=1):
            backups.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copy2(
                    str(self.path),
                    str(backups / ("progress-%s.db" % _dt.datetime.now().strftime("%Y%m%d-%H%M%S-%f"))),
                )
            except Exception:
                pass

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS steps (
                lesson_id TEXT, step_id TEXT,
                status TEXT DEFAULT 'new',          -- new | due | mastered
                attempts INTEGER DEFAULT 0,
                hints_used INTEGER DEFAULT 0,
                time_s REAL DEFAULT 0,
                independent_ok INTEGER DEFAULT 0,
                ease REAL DEFAULT 2.5,
                interval_days INTEGER DEFAULT 0,
                due TEXT,
                reps INTEGER DEFAULT 0,
                lapses INTEGER DEFAULT 0,
                last_result TEXT DEFAULT '',
                last_seen TEXT DEFAULT '',
                first_seen TEXT DEFAULT '',
                note TEXT DEFAULT '',
                PRIMARY KEY (lesson_id, step_id)
            );
            CREATE TABLE IF NOT EXISTS mistakes (
                lesson_id TEXT, step_id TEXT,
                my_sql TEXT DEFAULT '',
                correct_sql TEXT DEFAULT '',
                explanation TEXT DEFAULT '',
                repeat_count INTEGER DEFAULT 0,
                note TEXT DEFAULT '',
                created TEXT DEFAULT '',
                PRIMARY KEY (lesson_id, step_id)
            );
            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """
        )
        self.conn.commit()

    # -- facts ----------------------------------------------------------
    def learner_name(self) -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key='name'").fetchone()
        return row["value"] if row else ""

    def set_learner_name(self, name: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES('name',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (name,),
        )
        self.conn.commit()

    def step_row(self, lesson_id: str, step_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT * FROM steps WHERE lesson_id=? AND step_id=?",
            (lesson_id, step_id),
        ).fetchone()

    def record_attempt(
        self,
        lesson_id: str,
        step_id: str,
        *,
        passed: bool,
        hints: int,
        time_s: float,
        independent: bool = False,
    ) -> None:
        row = self.step_row(lesson_id, step_id)
        today_s = today()
        if row is None:
            self.conn.execute(
                "INSERT INTO steps(lesson_id, step_id, first_seen, last_seen) "
                "VALUES(?,?,?,?)",
                (lesson_id, step_id, today_s, today_s),
            )
            row = self.step_row(lesson_id, step_id)

        attempts = (row["attempts"] or 0) + 1
        hints_used = (row["hints_used"] or 0) + hints
        time_s_total = (row["time_s"] or 0) + time_s
        last_result = "pass" if passed else "fail"
        independent_ok = row["independent_ok"] or 0

        # SM-2 style scheduling
        quality = _quality(passed=passed, hints=hints, time_s=time_s)
        reps, ease, interval_days = _sm2((row["reps"] or 0), (row["ease"] or 2.5),
                                         (row["interval_days"] or 0), quality)
        prev_status = row["status"] or "new"
        status = prev_status
        if passed:
            independent_ok += 1 if independent else 0
            # mastery needs repeated independent success
            if independent_ok >= 2 and reps >= 2:
                status = "mastered"
            elif independent_ok >= 1:
                status = "due"
        else:
            independent_ok = max(0, independent_ok - 1)
            status = "due"

        # A failed step comes straight back today, so it can be fixed while
        # the mistake is still fresh (a same-day retry, not tomorrow's).
        if passed:
            due = (today_plus(interval_days)).isoformat() if interval_days else today_s
        else:
            due = today_s

        self.conn.execute(
            """
            UPDATE steps SET status=?, attempts=?, hints_used=?, time_s=?,
                independent_ok=?, ease=?, interval_days=?, due=?, reps=?,
                lapses=?, last_result=?, last_seen=? WHERE lesson_id=? AND step_id=?
            """,
            (status, attempts, hints_used, time_s_total, independent_ok, ease,
             interval_days, due, reps, (row["lapses"] or 0) + (0 if passed else 1),
             last_result, today_s, lesson_id, step_id),
        )
        self.conn.commit()

        self._award_xp(passed=passed, independent=independent,
                       newly_mastered=(status == "mastered" and prev_status != "mastered"))
        if passed and prev_status in ("due", "mastered"):
            self._bump_meta("reviews_done", 1)
        if not passed:
            self._touch_streak(carry=False)

    def note(self, lesson_id: str, step_id: str, text: str) -> None:
        self.conn.execute(
            "UPDATE steps SET note=? WHERE lesson_id=? AND step_id=?",
            (text, lesson_id, step_id),
        )
        self.conn.commit()

    def add_mistake(self, lesson_id: str, step_id: str, my_sql: str,
                    correct_sql: str, explanation: str, repeat_count: int = 0) -> None:
        self.conn.execute(
            """
            INSERT INTO mistakes(lesson_id, step_id, my_sql, correct_sql,
                explanation, repeat_count, created)
            VALUES(?,?,?,?,?,?,?)
            ON CONFLICT(lesson_id, step_id) DO UPDATE SET
                my_sql=excluded.my_sql, correct_sql=excluded.correct_sql,
                explanation=excluded.explanation, repeat_count=repeat_count+1
            """,
            (lesson_id, step_id, my_sql, correct_sql, explanation,
             repeat_count, today()),
        )
        self.conn.commit()

    def mistakes(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM mistakes ORDER BY created DESC LIMIT 200"
        ).fetchall()

    def clear_mistake(self, lesson_id: str, step_id: str) -> None:
        self.conn.execute(
            "DELETE FROM mistakes WHERE lesson_id=? AND step_id=?",
            (lesson_id, step_id),
        )
        self.conn.commit()

    # -- streaks ---------------------------------------------------------
    def streak(self) -> dict:
        row = self.conn.execute("SELECT value FROM meta WHERE key='streak'").fetchone()
        if row and row["value"]:
            try:
                return json.loads(row["value"])
            except Exception:
                pass
        return {"current": 0, "best": 0, "last": ""}

    def _save_streak(self, data: dict) -> None:
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES('streak',?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (json.dumps(data),),
        )
        self.conn.commit()

    def _touch_streak(self, carry: bool) -> None:
        """Called after a passed attempt. Extends the streak if it's new."""
        s = self.streak()
        last = _from_iso(s.get("last", ""), _dt.date.min)
        today_d = _dt.date.today()
        if last == today_d:
            current = s.get("current", 0)
        elif last == today_d - _dt.timedelta(days=1):
            current = s.get("current", 0) + 1
        else:
            current = 1 if carry else s.get("current", 0)
        best = max(s.get("best", 0), current)
        self._save_streak({"current": current, "best": best, "last": today_d.isoformat()})

    def on_passed(self) -> None:
        self._touch_streak(carry=True)

    # -- experience & levels ----------------------------------------------
    def _meta_get(self, key: str, default: str = "") -> str:
        row = self.conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
        return row["value"] if row and row["value"] is not None else default

    def _meta_set(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO meta(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
        self.conn.commit()

    def _bump_meta(self, key: str, amount: int) -> None:
        current = self._meta_get(key, "0")
        try:
            current_i = int(current)
        except Exception:
            current_i = 0
        self._meta_set(key, str(current_i + amount))

    def xp(self) -> int:
        try:
            return int(self._meta_get("xp", "0"))
        except Exception:
            return 0

    def add_xp(self, amount: int) -> None:
        self._bump_meta("xp", int(amount))

    def _award_xp(self, *, passed: bool, independent: bool,
                  newly_mastered: bool) -> None:
        gained = XP_PASS if passed else XP_FAIL
        if passed and independent:
            gained += XP_INDEPENDENT
        if newly_mastered:
            gained += XP_MASTERED
        self._bump_meta("xp", gained)

    def level_info(self) -> dict:
        return level_info(self.xp())

    # -- achievements -----------------------------------------------------
    def stats(self) -> dict:
        row = self.conn.execute(
            "SELECT COUNT(*) AS touched, "
            "SUM(CASE WHEN last_result='pass' THEN 1 ELSE 0 END) AS passed, "
            "SUM(CASE WHEN last_result='pass' AND hints_used=0 AND attempts=1 "
            "         THEN 1 ELSE 0 END) AS perfect, "
            "SUM(CASE WHEN status='mastered' THEN 1 ELSE 0 END) AS mastered, "
            "SUM(independent_ok) AS independent "
            "FROM steps"
        ).fetchone()
        touched = row["touched"] or 0
        lesson_row = self.conn.execute(
            "SELECT COUNT(DISTINCT lesson_id) AS n FROM steps").fetchone()
        mistakes = self.conn.execute(
            "SELECT COUNT(*) AS n FROM mistakes").fetchone()["n"]
        streak = self.streak()
        try:
            reviews_done = int(self._meta_get("reviews_done", "0"))
        except Exception:
            reviews_done = 0
        return {
            "passed": row["passed"] or 0,
            "perfect": row["perfect"] or 0,
            "mastered": row["mastered"] or 0,
            "independent": row["independent"] or 0,
            "touched": touched,
            "lessons_touched": lesson_row["n"] or 0,
            "mistakes": mistakes,
            "reviews_done": reviews_done,
            "streak_current": streak.get("current", 0),
            "streak_best": streak.get("best", 0),
            "level": self.level_info()["level"],
            "xp": self.xp(),
        }

    def achievements(self) -> list[str]:
        raw = self._meta_get("achievements", "")
        if not raw:
            return []
        try:
            data = json.loads(raw)
            return [str(x) for x in data] if isinstance(data, list) else []
        except Exception:
            return []

    def check_achievements(self) -> list[str]:
        """Compare progress with every badge rule; remember the new ones.

        Returns the ids of achievements *newly* earned on this call.
        """
        earned = _achievements.evaluate(self.stats())
        known = set(self.achievements())
        fresh = sorted(earned - known)
        if fresh:
            self._meta_set("achievements", json.dumps(sorted(known | earned)))
        return fresh

    def weak_spots(self, limit: int = 50) -> list[sqlite3.Row]:
        """Steps that keep tripping the learner up, worst first."""
        return self.conn.execute(
            "SELECT * FROM steps "
            "WHERE (lapses > 0 OR last_result='fail') "
            "ORDER BY lapses DESC, last_seen DESC LIMIT ?",
            (limit,),
        ).fetchall()

    # -- review lists -----------------------------------------------------
    def due_steps(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM steps WHERE status IN ('due','new') AND due<=? "
            "ORDER BY due ASC LIMIT 30",
            (today(),),
        ).fetchall()

    def due_step_ids(self) -> set[str]:
        return {r["step_id"] for r in self.due_steps()}

    def passed_count(self) -> int:
        """How many exercises are done (passed at least once)."""
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM steps WHERE status IN ('due','mastered')"
        ).fetchone()
        return row["n"] or 0

    def progress_summary(self, all_steps: list) -> dict:
        total = len(all_steps)
        done = 0
        mastered = 0
        for row in self.conn.execute("SELECT step_id,status FROM steps"):
            if row["status"] in ("due", "mastered"):
                done += 1
            if row["status"] == "mastered":
                mastered += 1
        return {"total": total, "done": done, "mastered": mastered,
                "percent": round(100 * done / total, 1) if total else 0.0}

    def export_json(self) -> str:
        data = {"meta": {}, "steps": [], "mistakes": []}
        for r in self.conn.execute(
            "SELECT * FROM steps ORDER BY lesson_id, step_id"
        ):
            data["steps"].append(dict(r))
        for r in self.conn.execute("SELECT * FROM mistakes"):
            data["mistakes"].append(dict(r))
        for r in self.conn.execute("SELECT * FROM meta"):
            data["meta"][r["key"]] = r["value"]
        return json.dumps(data, indent=2)

    def import_json(self, payload: str) -> dict:
        data = json.loads(payload)
        counts = {"steps": 0, "mistakes": 0, "meta": 0}
        for r in data.get("steps", []):
            self.conn.execute(
                """
                INSERT INTO steps(lesson_id, step_id, status, attempts, hints_used,
                    time_s, independent_ok, ease, interval_days, due, reps, lapses,
                    last_result, last_seen, first_seen, note)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(lesson_id, step_id) DO UPDATE SET
                    status=excluded.status, attempts=excluded.attempts,
                    hints_used=excluded.hints_used, time_s=excluded.time_s,
                    independent_ok=excluded.independent_ok, ease=excluded.ease,
                    interval_days=excluded.interval_days, due=excluded.due,
                    reps=excluded.reps, lapses=excluded.lapses,
                    last_result=excluded.last_result, last_seen=excluded.last_seen,
                    note=excluded.note
                """,
                (r.get("lesson_id", ""), r.get("step_id", ""), r.get("status", "new"),
                 r.get("attempts", 0), r.get("hints_used", 0), r.get("time_s", 0.0),
                 r.get("independent_ok", 0), r.get("ease", 2.5),
                 r.get("interval_days", 0), r.get("due", today()),
                 r.get("reps", 0), r.get("lapses", 0), r.get("last_result", ""),
                 r.get("last_seen", ""), r.get("first_seen", today()),
                 r.get("note", "")),
            )
            counts["steps"] += 1
        for r in data.get("mistakes", []):
            self.conn.execute(
                """
                INSERT INTO mistakes(lesson_id, step_id, my_sql, correct_sql,
                    explanation, repeat_count, note, created)
                VALUES(?,?,?,?,?,?,?,?)
                """,
                (r.get("lesson_id", ""), r.get("step_id", ""), r.get("my_sql", ""),
                 r.get("correct_sql", ""), r.get("explanation", ""),
                 r.get("repeat_count", 0), r.get("note", ""), r.get("created", today())),
            )
            counts["mistakes"] += 1
        for k, v in data.get("meta", {}).items():
            self.conn.execute(
                "INSERT INTO meta(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (k, v),
            )
            counts["meta"] += 1
        self.conn.commit()
        return counts

    def reset_practice_data(self) -> None:
        self.conn.execute("DELETE FROM steps")
        self.conn.execute("DELETE FROM mistakes")
        self.conn.execute("DELETE FROM meta WHERE key IN "
                          "('streak','xp','achievements','reviews_done')")
        self.conn.commit()


def today_plus(days: int) -> _dt.date:
    return _dt.date.today() + _dt.timedelta(days=days)


def level_info(xp: int) -> dict:
    """Turn raw XP into a level, a title and progress towards the next level.

    Each level costs a little more than the one before (level 1 needs 100,
    level 2 needs 200, level 3 needs 300…), so early wins feel fast.
    """
    xp = max(0, int(xp or 0))
    level = 1
    need = 0
    while xp >= need + 100 * level:
        need += 100 * level
        level += 1
    span = 100 * level
    into = xp - need
    title = LEVEL_TITLES[min(level - 1, len(LEVEL_TITLES) - 1)]
    return {
        "level": level,
        "title": title,
        "xp": xp,
        "into_level": into,
        "span": span,
        "next_at": need + span,
        "to_next": span - into,
    }


def _quality(*, passed: bool, hints: int, time_s: float) -> int:
    """0-5 rating for SM-2. Guesswork/hints/time punish the score."""
    if not passed:
        if hints >= 3:
            return 0
        return 1
    if hints == 0:
        return 5
    if hints == 1:
        return 4
    if hints == 2:
        return 3
    return 2


def _sm2(reps: int, ease: float, interval_days: int, quality: int):
    """Classic SM-2 scheduling; returns (reps, ease, interval_days)."""
    if quality < 3:
        reps = 0
        interval_days = 1
        ease = max(1.3, ease - 0.2)
        return reps, ease, interval_days
    reps += 1
    if reps == 1:
        interval = 1
    elif reps == 2:
        interval = 3
    elif reps == 3:
        interval = 7
    elif reps == 4:
        interval = 14
    else:
        interval = round(interval_days or 1) * ease
    interval = int(interval)
    ease = ease + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    ease = max(1.3, ease)
    return reps, ease, interval


def empty_path_check(db_path: Path) -> bool:
    """True when the store file exists and has the expected tables."""
    try:
        c = sqlite3.connect(str(db_path))
        row = c.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='steps'").fetchone()
        c.close()
        return bool(row and row[0])
    except Exception:
        return False


__all__ = ["ProgressStore", "today", "today_plus", "_sm2", "_quality",
           "level_info", "XP_PASS", "XP_INDEPENDENT", "XP_MASTERED", "XP_FAIL"]