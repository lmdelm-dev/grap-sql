"""Generate data/lessons/*.json from the lesson definitions, then verify.

Every reference solution is executed against a fresh copy of the practice
shop and must PASS the same grader the learner uses.  Anything that fails is
printed loudly - no broken lesson ships.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools import lessons_a, lessons_b, lessons_gen  # noqa: E402

LESSONS = lessons_a.LESSONS + lessons_b.LESSONS + lessons_gen.LESSONS

# Steps whose whole point is one taught feature: pass the rows AND use it.
REQUIREMENTS = {
    ("L05", 1): ["order by"], ("L05", 2): ["order by"], ("L05", 3): ["order by"],
    ("L06", 1): ["limit"], ("L06", 2): ["limit"], ("L06", 3): ["limit"],
    ("L08", 2): ["group by"], ("L08", 4): ["group by"],
    ("L09", 1): ["join"], ("L09", 3): ["join"], ("L09", 5): ["join"],
    ("L10", 1): ["left join"], ("L10", 2): ["left join"],
    ("L11", 1): ["insert"], ("L11", 5): ["insert"],
    ("L12", 1): ["update"], ("L12", 2): ["update"],
    ("L13", 1): ["delete"],
    ("L20", 3): ["join"],
}


def _apply_requirements() -> None:
    for lesson in LESSONS:
        for i, step in enumerate(lesson["steps"], start=1):
            required = REQUIREMENTS.get((lesson["id"], i))
            if required:
                step.setdefault("check", {})["require"] = required


_apply_requirements()


def emit(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for lesson in LESSONS:
        path = out_dir / ("%s.json" % lesson["id"])
        path.write_text(json.dumps(lesson, indent=2, ensure_ascii=False), encoding="utf-8")
        print("wrote", path.name)


def verify() -> list[str]:
    """Run every reference solution through the real grader."""
    from sqlschool.db.sandbox import Sandbox
    from sqlschool.lessons.loader import load_lessons

    problems = []
    lessons, load_problems = load_lessons()
    problems += load_problems

    a = Sandbox()
    b = Sandbox()
    try:
        for lesson in lessons:
            for step in lesson.steps:
                if step.kind in ("type", "build", "fix") or (
                    step.kind == "fill" and step.expected_sql
                ):
                    a.reset()
                    b.reset()
                    try:
                        _check_reference(lesson.id, step, problems, a, b)
                    except Exception as exc:  # noqa: BLE001
                        problems.append(
                            "%s/%s reference crashed: %s" % (lesson.id, step.id, exc)
                        )
    finally:
        a.close()
        b.close()
    return problems


def _check_reference(lesson_id, step, problems, a, b) -> None:
    from sqlschool.engine import grader

    expected = step.reference_solution()
    res = a.run(expected)
    if not res.ok:
        problems.append("%s/%s reference solution failed to run: %s"
                        % (lesson_id, step.id, res.message))
        return
    if step.check.get("demo"):
        return
    if step.check.get("any_rows"):
        if res.kind == "select" and res.rows:
            return
        problems.append("%s/%s expected rows but got none" % (lesson_id, step.id))
        return
    ref_res = b.run(expected)
    if res.kind == "select" and ref_res.kind == "select":
        verdict = grader.compare_select(res.columns, res.rows,
                                        ref_res.columns, ref_res.rows,
                                        reference_sql=expected,
                                        learner_sql=expected)
    elif res.kind == "modify" and ref_res.kind == "modify":
        verdict = grader.compare_state(res.state or {}, ref_res.state or {})
    else:
        verdict = grader.Verdict.fail("kind mismatch", "")
    if not verdict.passed:
        problems.append("%s/%s reference does not pass itself: %s"
                        % (lesson_id, step.id, verdict.comparison))


if __name__ == "__main__":
    from sqlschool.paths import lessons_dir

    emit(lessons_dir())       # write the JSON first…
    problems = verify()       # …then run the real gate over what ships
    if problems:
        print("PROBLEMS (%d):" % len(problems))
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("All %d lessons verified OK." % len(LESSONS))