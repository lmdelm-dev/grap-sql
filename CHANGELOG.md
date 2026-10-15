# Changelog

All notable changes to **GRAP-SQL** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-15

The first public release of GRAP-SQL — a calm, fully offline terminal that
teaches SQL from absolute zero.

### Added
- Three-pane learning window: **Teacher** (explains, hints, translates your
  query), **Type here** (a real SQL terminal with syntax highlighting, ghost
  text and typing feedback) and **Output** (the real result of your query).
- **327 lessons / 10,487 exercises** covering `SELECT` through joins, grouping,
  sub-queries and `INSERT` / `UPDATE` / `DELETE` / `CREATE TABLE`.
- A real **SQLite practice shop** (7 tables) with a safe in-memory sandbox
  (`ATTACH`/`PRAGMA`/`load_extension` denied, time budget, row cap, one-click
  reset).
- **Result-based grading** — order-tolerant, alias-aware, float tolerance,
  NULL handling; DML compared by final table state, not by text.
- **Spaced repetition** (SM-2): failed steps come back the same day; passes are
  rescheduled across 1 → 3 → 7 → 14 days.
- XP, **levels** and 14 **achievements**.
- **Adaptive challenge mode**, exercise **search**, **weak spots**, a
  **mistake notebook** and a **review-today** queue.
- **SQL reference** and **schema browser** cards; optional **Pro console**.
- Automatic **progress backups** + JSON **export/import**.
- Light and dark themes, adjustable text size, and a "reduce motion" option.
- **About** dialog with credits.

### Branding
- Named **GRAP-SQL**; author **Jamal Tiliouan**.
- New mark: a **half pen** — a fountain-pen nib split left/right, drawn live in
  the app's own colours. Used as the window icon and in the Welcome/About views.
- Progress now lives in `~/.grap-sql/`; an earlier `.sql_terminal_school/`
  folder is adopted automatically so no progress is lost.

### Packaging
- `run.bat` for a zero-friction Windows launch (installs dependencies once).
- `build_exe.bat` + `GRAP-SQL.spec` to build a standalone
  `GRAP-SQL.exe` with PyInstaller.
- `pyproject.toml`, `LICENSE` (MIT), GitHub Actions CI and this changelog.

[1.0.0]: https://github.com/lmdelm-dev/grap-sql/releases/tag/v1.0.0
