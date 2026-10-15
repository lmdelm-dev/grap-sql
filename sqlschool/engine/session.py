"""LessonSession - the loop the UI runs on every step.

The learner never needs to think about this loop:

1. the Teacher says what to type
2. the learner types it and presses Run / Ctrl+Enter
3. Output shows the real result
4. we grade by *result* (not text)
5. the Teacher explains their actual query, kindly
6. one memory trick
7. progress + the spaced-review clock are updated quietly
"""
from __future__ import annotations

import re
import time
import traceback
from dataclasses import dataclass, field

from ..db.sandbox import QueryResult, Sandbox
from ..db import safety
from ..engine import explain, grader
from ..engine.errors import friendly_error
from ..lessons.model import Lesson, Step
from ..memory.store import ProgressStore

BLANK_PATTERNS = [("___", "…"), ("____", "…"), ("??", "…")]


@dataclass
class RunOutcome:
    step: Step
    sql: str
    result: QueryResult
    verdict: grader.Verdict | None
    passed: bool
    teacher_lines: list[str]      # shown in the Teacher pane
    hint_level: int               # how many hints were shown for this attempt
    first_time: bool = True       # first attempt ever for this step
    mistake_recorded: bool = False
    new_achievements: list[str] = field(default_factory=list)


class LessonSession:
    """Drives one lesson step-by-step. Stateless except for sandbox + store."""

    def __init__(self, lesson: Lesson, sandbox: Sandbox, store: ProgressStore,
                 type_along: bool = True, reduce_motion: bool = False):
        self.lesson = lesson
        self.sandbox = sandbox
        self.store = store
        self.type_along = type_along
        self.reduce_motion = reduce_motion
        self.hints_shown = 0
        self.attempts = 0

    # -- navigation -----------------------------------------------------
    @property
    def step(self) -> Step | None:
        return self._step

    def load_step(self, index: int) -> Step:
        self.step_index = index
        self.hints_shown = 0
        self.attempts = 0
        # Each exercise starts from the original shop: exercises are
        # self-contained, and DML steps always grade against pristine state.
        self.sandbox.reset()
        self._step = self.lesson.steps[index]
        return self._step

    def step_count(self) -> int:
        return len(self.lesson.steps)

    # -- hints -----------------------------------------------------------
    def next_hint(self) -> str | None:
        hints = self.step.hints
        if self.hints_shown >= len(hints):
            return None
        level = self.hints_shown + 1  # 1-based hint level
        hint = hints[level - 1]
        self.hints_shown = level
        header = {
            1: "Think…",
            2: "A little closer…",
            3: "Nearly there…",
            4: "Last nudge…",
        }.get(level, "Hint")
        return "%s (hint %d of %d): %s" % (header, level, len(hints), hint.text)

    def preview_solution(self) -> str:
        return self.step.reference_solution()

    # -- running ----------------------------------------------------------
    def prepare_editor(self, step: Step) -> dict:
        """What the editor should show when a step starts."""
        if step.kind == "fill":
            return {"text": step.seed_sql, "ghost": None, "mode": "fill"}
        if step.kind == "fix":
            return {"text": step.seed_sql, "ghost": None, "mode": "fix"}
        if step.kind in ("answer", "predict"):
            return {"text": "", "ghost": None, "mode": "answer"}
        return {"text": "", "ghost": step.reference_solution() if self.type_along else None,
                "mode": "type"}

    def run(self, learner_text: str, have_typed: bool = False) -> RunOutcome:
        """Run the learner's answer through the sandbox and grade it."""
        step = self.step
        started = time.monotonic()
        self.attempts += 1
        hints = self.hints_shown

        if step.kind in ("answer", "predict"):
            return self._run_answer(step, learner_text, hints, started)

        provided = learner_text
        if step.kind in ("fill", "fix"):
            provided = learner_text

        if not provided.strip():
            return self._soft_fail(
                step, learner_text,
                "There's nothing to run yet. Try typing what the Teacher "
                "suggested, or press Hint for a nudge.",
                hints, started,
            )

        # BLANK check for fill
        if step.kind == "fill":
            for blank, _ in BLANK_PATTERNS:
                if blank in provided:
                    return self._soft_fail(
                        step, provided,
                        "Almost! You still have a blank (%s) left to fill in. "
                        "Replace it with the correct word." % blank,
                        hints, started,
                    )

        result = self.sandbox.run(provided)
        if not result.ok:
            lines = ["⚠ Almost!", "The database couldn't run that yet, and I looked "
                                "up what it meant so you can fix it fast:"]
            if result.message:
                lines.append(result.message)
            lines.append("Reset (the little ↺ button) puts the shop back to "
                         "original if you changed it.")
            outcome = RunOutcome(
                step=step, sql=provided, result=result, verdict=None,
                passed=False, teacher_lines=lines, hint_level=hints,
            )
            self._record_fail(step, provided, hints, started)
            return outcome

        verdict = self._grade(step, provided, result)

        # Optional "must use this feature" enforcement (kind but firm).
        required = step.check.get("require") or []
        if verdict and verdict.passed and required:
            missing = [clause for clause in required
                       if not re.search(r"\b%s\b" % _safe_clause(clause),
                                        provided, re.IGNORECASE)]
            if missing:
                verdict = grader.Verdict.fail(
                    "missing %s" % missing[0],
                    "You got the right rows - nice! But this step is here to "
                    "teach you %s. Add it to your query and run again."
                    % missing[0],
                )
        lines = self._teacher_explanation(step, provided, result, verdict)

        passed = bool(verdict and verdict.passed)
        # demo steps pass when they simply ran without error
        if not passed and step.check.get("demo"):
            passed = True
            verdict = grader.Verdict.pass_("ran successfully (demo step)",
                                           "This step's goal was simply to see a query run.")

        outcome = RunOutcome(
            step=step, sql=provided, result=result, verdict=verdict,
            passed=passed, teacher_lines=lines, hint_level=hints,
        )
        if passed:
            self.store.on_passed()
        self._record_attempt(step, provided, passed, hints, started)
        outcome.new_achievements = self.store.check_achievements()
        return outcome

    # -- grading -----------------------------------------------------------
    def _grade(self, step: Step, sql: str, result: QueryResult):
        # reference: run in a separate sandbox so the learner copy stays untouched
        ref = Sandbox(time_ms=self.sandbox.time_ms)
        try:
            if step.kind == "answer":
                return grader.Verdict.pass_("text answer") if _answer_ok(step, sql) else grader.Verdict.fail("text mismatch")
            expected = step.reference_solution()

            if step.check.get("any_rows"):
                if result.kind == "select" and result.rows:
                    return grader.Verdict.pass_("returns rows",
                                                "Your query returned %d row%s." % (
                                                    len(result.rows),
                                                    "s" if len(result.rows) != 1 else ""))
                return grader.Verdict.fail("no rows",
                                           "Your query ran, but returned no rows. "
                                           "That's about seeing the data, so try "
                                           "removing filters and ask for more columns.")

            ref_res = ref.run(expected)
            if not ref_res.ok:
                # The reference itself is broken; say so honestly.
                from ..lessons.model import validate_step
                return grader.Verdict.fail(
                    "reference broke",
                    "Hmm, the reference solution for this step hit a database "
                    "problem too. This is our bug - please go to the next step."
                )

            if result.kind == "select" and ref_res.kind == "select":
                return grader.compare_select(
                    result.columns, result.rows,
                    ref_res.columns, ref_res.rows,
                    reference_sql=expected, learner_sql=sql,
                )
            if result.kind == "modify" and ref_res.kind == "modify":
                return grader.compare_state(result.state or {}, ref_res.state or {})
            return grader.Verdict.fail(
                "query kind mismatch",
                "This question asked you to %s some data, and your query only "
                "%s. Read the task again and match the action."
                % (_friendly_verb(expected), _friendly_verb(sql)),
            )
        finally:
            ref.close()

    # -- teacher output -----------------------------------------------------
    def _teacher_explanation(self, step, sql, result, verdict) -> list[str]:
        lines = []
        if verdict is None:
            lines.append("Here's what that did:")
        elif verdict.passed:
            first = {
                "select": "✓ Nice work! Your query did the job.",
                "modify": "✓ Nice work! The shop now looks like the answer.",
            }.get(result.kind, "✓ Nice work!")
            lines.append(first)
        else:
            lines.append("⚠ Almost! Your query ran, but the answer doesn't match "
                         "the target yet. Here's what I noticed:")
            if verdict.comparison:
                lines.append("• " + (verdict.detail or verdict.comparison))

        transl = explain.explain_sql(result.sql or sql)
        if transl:
            lines.append("")
            lines.append("What you wrote, in plain words:")
            for t in transl:
                lines.append("  %s → %s" % (t["word"], t["english"]))
        elif result.ok and step.kind == "sql":
            lines.append("")
            lines.append("I understood the query structure, but not deeply "
                         "enough to translate it line by line yet.")

        if verdict and verdict.passed and step.memory_trick:
            lines.append("")
            lines.append("🧠 Memory trick: " + step.memory_trick)
        elif not verdict or not verdict.passed:
            lines.append("")
            lines.append("🧠 Memory trick: " + (step.memory_trick or "read your "
                         "query out loud, one line at a time - the words are "
                         "almost English already."))
        return lines

    def _run_answer(self, step, text, hints, started) -> RunOutcome:
        ok = _answer_ok(step, text)
        result = QueryResult(ok=ok, sql="", columns=[], rows=[])
        result.kind = "select"
        verdict = grader.Verdict.pass_("answer matches") if ok else grader.Verdict.fail("answer mismatch")
        lines = []
        if ok:
            lines.append("✓ Nice work, that's right!")
        else:
            accepted = ", ".join(str(a) for a in (step.check.get("answer") or []))
            lines.append("⚠ Almost! The right answer is one of: %s." % accepted)
        if step.extra:
            lines.append("")
            lines.append(step.extra)
        if ok and step.memory_trick:
            lines.append("")
            lines.append("🧠 Memory trick: " + step.memory_trick)
        outcome = RunOutcome(step=step, sql=text, result=result, verdict=verdict,
                             passed=ok, teacher_lines=lines, hint_level=hints)
        if ok:
            self.store.on_passed()
        self._record_attempt(step, text, ok, hints, started)
        outcome.new_achievements = self.store.check_achievements()
        return outcome

    def _soft_fail(self, step, text, msg, hints, started) -> RunOutcome:
        result = QueryResult(ok=False, sql=text, error="empty", message=msg)
        outcome = RunOutcome(step=step, sql=text, result=result, verdict=None,
                             passed=False, teacher_lines=["⚠ Almost!", msg],
                             hint_level=hints)
        self._record_fail(step, text, hints, started)
        return outcome

    # -- recording ----------------------------------------------------------
    def _record_attempt(self, step, sql, passed, hints, started) -> None:
        independent = not self.type_along and hints == 0 and self.attempts <= 2
        time_s = time.monotonic() - started
        self.store.record_attempt(self.lesson.id, step.id, passed=passed,
                                  hints=hints, time_s=time_s, independent=independent)
        if not passed:
            ref = Step(kind="type", id=step.id, title="", prompt="",
                       expected_sql=step.reference_solution())
            self.store.add_mistake(
                self.lesson.id, step.id, sql or "(nothing typed)",
                step.reference_solution(),
                "Recorded from step %s - practice it again soon." % step.id,
            )

    def _record_fail(self, step, sql, hints, started) -> None:
        self._record_attempt(step, sql, False, hints, started)


# Example "require" markers are simple lower-case clause phrases.

def _safe_clause(clause: str) -> str:
    """Braces for a lowercase clause keyword given by a lesson author."""
    return re.sub(r"[^a-z]+", r"\\s+", clause.lower())


def _answer_ok(step: Step, text: str) -> bool:
    accepted = step.check.get("answer") or []
    if isinstance(accepted, str):
        accepted = [accepted]
    cleaned = text.strip().strip("'").strip('"').lower()
    for a in accepted:
        if str(a).strip().strip("'").strip('"').lower() == cleaned:
            return True
    return False


def _friendly_verb(sql: str) -> str:
    try:
        return {"select": "look at", "insert": "add", "update": "change",
                "delete": "remove", "create": "build", "drop": "remove"}.get(
                explain.statement_kind(sql), "work with")
    except Exception:
        return "work with"