"""The Output pane (bottom right): terminal-style messages + the real table."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..theme import Palette
from .widgets import PaneFrame, ResultTable


class OutputPane(PaneFrame):
    reset_requested = Signal()

    def __init__(self, pal: Palette, parent=None):
        super().__init__("4 · Output", pal, parent)
        self.pal = pal

        top = QHBoxLayout()
        self.rownote = QLabel("")
        self.rownote.setObjectName("paneTitle")
        top.addWidget(self.rownote)
        top.addStretch(1)
        clear = QPushButton("⌫ Clear")
        clear.setObjectName("ghost")
        clear.setToolTip("Clear the messages and the result table.")
        clear.clicked.connect(self.clear_all)
        self.clear_button = clear
        top.addWidget(clear)
        reset = QPushButton("↺ Reset")
        reset.setObjectName("ghost")
        reset.setToolTip("Put the practice shop back to its original state.")
        reset.clicked.connect(self.reset_requested)
        self.reset_button = reset
        top.addWidget(reset)
        self.body.addLayout(top)

        self.messages = QTextBrowser()
        self.messages.setObjectName("pane")
        self.messages.setMaximumHeight(170)
        self.messages.setOpenLinks(False)
        self.messages.document().setDefaultStyleSheet(_msg_css(pal))
        self.body.addWidget(self.messages, 0)

        self.result = ResultTable()
        self.body.addWidget(self.result, 1)
        self.sync_with_theme()

    # -- public API ------------------------------------------------------
    def clear_all(self) -> None:
        self.messages.clear()
        self.rownote.setText("")
        self.result.hide()

    def clear_messages(self) -> None:
        self.messages.clear()
        self.result.hide()

    def append_line(self, text: str, kind: str = "info") -> None:
        cls = {"ok": "ok", "warn": "warn", "err": "err", "think": "think",
               "info": "info", "accent": "accent"}.get(kind, "info")
        esc = _html_escape(text)
        prefix = {
            "ok": "✓ ", "warn": "⚠ ", "err": "✗ ", "think": "● ", "info": "  ",
            "accent": "❯ ",
        }[cls]
        self.messages.append('<span class="%s">%s%s</span>' % (cls, prefix, esc))
        self.messages.moveCursor(QTextCursor.MoveOperation.End)

    def append_html(self, html: str) -> None:
        self.messages.append(html)
        self.messages.moveCursor(QTextCursor.MoveOperation.End)

    def show_thinking(self) -> None:
        self.append_line("Thinking…", kind="think")

    def show_result_table(self, columns, rows, row_note="", truncated=False) -> None:
        self.rownote.setText(row_note + (" · capped at 1000" if truncated else ""))
        self.result.show_result(columns, rows)
        self.result.show()

    def show_status(self, text: str) -> None:
        self.rownote.setText(text)
        self.result.hide()

    def sync_with_theme(self) -> None:
        self.messages.document().setDefaultStyleSheet(_msg_css(self.pal))


def _msg_css(pal: Palette) -> str:
    return """
    span.ok { color: %s; }
    span.warn { color: %s; }
    span.err { color: %s; }
    span.think { color: %s; }
    span.info { color: %s; }
    span.accent { color: %s; }
    """ % (pal.success, pal.hint, pal.error, pal.muted, pal.muted, pal.accent)


def _html_escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))