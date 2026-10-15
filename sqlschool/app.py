"""Launch GRAP-SQL.

Run with::

    python -m sqlschool
    # or simply:  python app.py

The app is fully offline.  Settings and progress live next to each other in
``~/.grap-sql/``.
"""
from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from . import APP_AUTHOR, APP_NAME, APP_VERSION
from .config import Settings
from .db.sandbox import Sandbox
from .lessons.loader import load_lessons
from .memory.store import ProgressStore
from .paths import practice_db_path
from .theme import PALETTES, mono_family, qss
from .ui.logo import logo_icon
from .ui.main_window import MainWindow


def build_app() -> QApplication:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)
    app.setOrganizationDomain("grap-sql.local")
    pal = PALETTES.get(Settings.load().theme, PALETTES["dark"])
    app.setWindowIcon(logo_icon(pal))
    return app


def make_window(settings: Settings | None = None, sandbox: Sandbox | None = None,
                store: ProgressStore | None = None):
    """Create the main window (used by both the app and the UI smoke tests)."""
    settings = settings or Settings.load()
    lessons, problems = load_lessons()
    sandbox = sandbox or Sandbox()
    store = store or ProgressStore()
    pal = PALETTES.get(settings.theme, PALETTES["dark"])

    def _zoom(delta: int) -> None:
        if delta == 0:
            # settings (theme etc.) changed
            pal = PALETTES.get(settings.theme, PALETTES["dark"])
            _app = QApplication.instance()
            if _app is not None:
                _app.setStyleSheet(qss(pal, settings.font_size))
            for win in _win:
                win.pal = pal
                win.apply_palette()
            return
        settings.font_size = max(11, min(26, settings.font_size + delta))
        settings.save()
        pal = PALETTES.get(settings.theme, PALETTES["dark"])
        _app = QApplication.instance()
        if _app is not None:
            _app.setStyleSheet(qss(pal, settings.font_size))
        for win in _win:
            win.pal = pal
            win.set_font_size(settings.font_size)
            win.apply_palette()

    _win: list[MainWindow] = []
    win = MainWindow(settings, lessons, sandbox, store, pal,
                     zoom_cb=_zoom, data_hook=(settings, lessons))
    _win.append(win)
    win.pal = pal
    if problems:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QMessageBox, QLabel, QDialog, QVBoxLayout
        # Report skipped / broken lessons kindly, without stopping the app.
        def _warn() -> None:
            dlg = QDialog(win)
            dlg.setWindowTitle("A friendly heads-up")
            lay = QVBoxLayout(dlg)
            lay.addWidget(QLabel(
                "I couldn't load a few lesson files, so I skipped them so "
                "you can keep learning:\n\n%s\n\nEverything else is ready."
                % "\n".join(problems[:8])))
            got = QLabel("(This only happens when a lesson file is damaged.)")
            got.setObjectName("paneTitle")
            lay.addWidget(got)
            dlg.exec()
        QTimer.singleShot(800, _warn)
    return win


def main() -> int:
    app = build_app()
    settings = Settings.load()
    from .theme import PALETTES

    pal = PALETTES.get(settings.theme, PALETTES["dark"])
    app.setStyleSheet(qss(pal, settings.font_size))
    # Nice monospace everywhere inside the typing/output panes.
    fam = mono_family()

    win = make_window(settings)
    win.show()
    code = app.exec()
    return code


if __name__ == "__main__":
    raise SystemExit(main())