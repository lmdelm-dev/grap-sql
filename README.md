# GRAP-SQL

[![tests](https://github.com/lmdelm-dev/grap-sql/actions/workflows/tests.yml/badge.svg)](https://github.com/lmdelm-dev/grap-sql/actions/workflows/tests.yml)
[![license: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![GUI: PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://pypi.org/project/PySide6/)

A calm, three-pane terminal that teaches you SQL from zero — all offline, all real.

**Author: Jamal Tiliouan.**

It is a **real database**, not a simulation. You type actual SQL into a terminal,
press Run, and the app executes your query against a genuine copy of a little
Moroccan shop database — and the Teacher explains your query back to you in
plain words.

---

## Getting started (for non-coders)

**Easiest — no install:** grab the standalone build from the
[Releases page](https://github.com/lmdelm-dev/grap-sql/releases/latest), unzip
it, and double-click `GRAP-SQL.exe`.

**From source:**

1. Install **Python** from <https://www.python.org/downloads/> — during
   installation, tick **“Add python.exe to PATH”**.
2. Double-click **`run.bat`**. The first time, it installs the small libraries
   the app needs (you'll see a black window for a minute — that's normal).
3. That's it. The app opens. Every future time, just double-click `run.bat`.

> GRAP-SQL works fully offline. It never phones home, and nothing you type ever
> leaves your computer.

---

## A quick tour

The window has three panes:

| Pane | What it does |
| ---- | ------------ |
| **Teacher** | Speaks first, explains every step, gives hints, and translates *your* query into plain English afterwards. |
| **Type here** | Your terminal. A ghost of the example fades in as you type; a coral block cursor blinks where you are. |
| **Output** | The real result of your query — rows, messages, and explanations from the Teacher. |

Common controls:

- **Run** (or press `Ctrl+Enter`) — run what you typed.
- **Hint** — up to 4 increasingly specific hints.
- **Type it for me** (or `Ctrl+P`) — fills the typing box with the example.
- **⌫ Clear / ↺ Reset** — clear the output, or put the shop back to its original state.
- **Next →** — only lights up once your answer is actually correct.
- **☰ Menu** (or `Esc`) — lessons map, search, challenge mode, progress,
  achievements, weak spots, mistakes, review, SQL reference, schema browser,
  Pro console, settings, export/import, and **About**.
- **Ctrl +/-** — make the text bigger or smaller.

### How a step works

1. The Teacher says what to do — sometimes it's a question, sometimes a
   line of SQL to type.
2. You type SQL in the terminal and press **Run**.
3. The Output shows the **real** result, and grading is by *result*:
   two completely different queries that return the right data both pass.
4. The Teacher then explains **your** query, line by line, plus one memory trick.
5. Progress is remembered with a **spaced-repetition clock** (1 → 3 → 7 → 14
   days): the app quietly brings back old steps before they fade.

There are **327 lessons** with **10,487 exercises**, from your first `SELECT`
to joins, grouping, sub-queries, `INSERT`/`UPDATE`/`DELETE` and `CREATE TABLE`.

---

## Where your progress lives

- Settings + progress: a folder called `.grap-sql` in your home folder
  (`C:\Users\<you>\.grap-sql`). If you used an earlier build, its
  `.sql_terminal_school` folder is adopted automatically — your progress is
  never lost in a rename.
- Your progress is **backed up automatically** into `backups/`. If the progress
  file ever gets damaged, the app recovers it automatically and keeps a copy of
  the broken file (`progress-corrupt-*.db`) so nothing is silently lost.
- **Export / Import** (in the ☰ menu) saves everything — progress, streaks,
  mistakes — as a single JSON file you can move to another computer.

---

## For curious coders

```
sqlschool/
  app.py            # window wiring, themes, zoom
  engine/
    sandbox.py      # safe SQLite runner (in-memory copy, ATTACH/PRAGMA denied,
                    #   time budget, row cap, reset-to-original)
    grader.py       # result-based grading: order-tolerant, aliases, float
                    #   tolerance, NULLs, DML compared by final table state
    explain.py      # line-by-line “what you wrote” translation
    session.py      # the run → grade → explain → remember loop (+ hint levels)
    errors.py       # friendly SQL error messages with spelling suggestions
  ui/               # Editor, Teacher, Output panes, dialogs, main window, logo
  lessons/          # loader + step model (lessons are plain JSON)
  memory/store.py   # SM-2 spaced repetition, streaks, mistakes, backups,
                    #   export/import
  db/practice/…     # the pristine shop database (never modified)
data/lessons/       # 327 lessons as readable JSON
tools/author_lessons.py  # re-emits lesson JSON and then *verifies* it by
                    #   running every reference solution through the real grader
tests/              # pytest suite (headless)
```

- Run the tests: double-click **`run_tests.bat`** (no window appears), or:
  `python -m pytest tests`
- Re-author + verify lessons: `python tools/author_lessons.py`
  (must print `All 327 lessons verified OK.`)

### Safety of the sandbox

Everything you type runs on a **fresh in-memory copy** of the shop database:

- `ATTACH` / `DETACH` (reaching other files) and `load_extension` are refused.
- A time budget aborts runaway queries; a row cap stops giant result sets.
- The slate is cleaned (reset) at the start of each exercise, and the ↺ button
  always restores the original data.

### Grading philosophy

We grade the **result, not the text**. If your query returns the right rows
(any order, any aliases, floats within tolerance), it's right. When a step is
*didactic* (e.g. “this lesson is about `ORDER BY`”), the app kind of insists the
taught feature appears — that's the `require` rule on a handful of steps.

### Building a standalone app (optional)

To produce a single `GRAP-SQL.exe` that runs without a Python install, use the
included PyInstaller spec:

```
pip install pyinstaller
build_exe.bat
```

The result appears in `dist/GRAP-SQL/`.

### Known limitations

- **NoSQL World 2** (a planned second course on non-relational databases) is
  not built yet — this release is purely SQL.
- The app ships with the practice “Moroccan shop” dataset only; there's no
  import-your-own-csv feature yet.

---

## Credits

- **Author & designer:** Jamal Tiliouan.
- **Built with:** Python, PySide6 (Qt) and SQLite; explanations use sqlglot.
- **The mark:** a half pen — a fountain-pen nib split left/right, drawn live in
  the app's own colours.

Made for people who find databases scary. Be kind to your terminal. 🐢
