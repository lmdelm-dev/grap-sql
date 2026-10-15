"""The lesson engine's data model: what a lesson and a step look like."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Hint:
    level: int    # 1..4, increasingly specific
    text: str


@dataclass
class Step:
    kind: str                # type | fill | fix | predict | answer | build
    id: str                  # e.g. "L01-2"
    title: str               # short, e.g. "Your first SELECT"
    prompt: str              # teacher explanation, plain words
    real_life: str = ""      # real-life comparison
    memory_trick: str = ""   # one mnemonic
    task: str = ""           # exact words: "Try typing:"
    expected_sql: str = ""   # reference solution
    seed_sql: str = ""       # pre-filled / to-fix code
    ordered: bool = False    # does row order matter?
    check: dict = field(default_factory=dict)
    hints: list[Hint] = field(default_factory=list)
    extra: str = ""          # extra teaching text shown after grading

    def reference_solution(self) -> str:
        return (self.expected_sql or self.seed_sql).strip()


@dataclass
class Lesson:
    id: str
    title: str
    order: int
    difficulty: int
    concept_tags: list[str]
    steps: list[Step]

    @property
    def step_count(self) -> int:
        return len(self.steps)


def validate_step(step: Step, lesson_id: str) -> list[str]:
    """Return a list of problems, empty when the step is usable."""
    problems = []
    if not step.prompt.strip():
        problems.append("%s/%s: prompt is empty" % (lesson_id, step.id))
    if step.kind in ("type", "fill", "fix", "build") and not step.reference_solution():
        if not (step.check or {}).get("any_rows"):
            problems.append("%s/%s: no reference solution and no check" % (lesson_id, step.id))
    if not step.hints:
        problems.append("%s/%s: step has no hints" % (lesson_id, step.id))
    levels = [h.level for h in step.hints]
    if sorted(levels) != [1, 2, 3, 4]:
        problems.append("%s/%s: hints must be levels 1,2,3,4" % (lesson_id, step.id))
    return problems