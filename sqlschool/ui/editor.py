"""The "Type here" pane: a terminal-feeling SQL editor.

* SQL syntax highlighting (soft palette: keywords coral, identifiers soft
  blue when they are real tables/columns, strings sage, numbers sand,
  comments grey)
* a softly blinking block cursor in coral
* grey "ghost text" to type over in early lessons; it turns green as the
  learner types the correct prefix, coral otherwise
* placeholder text doubles as the terminal prompt ``❯``
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QRegularExpression, QTimer
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit

from ..theme import Palette

SQL_KEYWORDS = [
    "select", "from", "where", "group", "by", "order", "having", "limit",
    "offset", "join", "inner", "left", "right", "outer", "cross", "full",
    "on", "and", "or", "not", "in", "is", "null", "like", "between",
    "as", "asc", "desc", "distinct", "insert", "into", "values", "update",
    "set", "delete", "create", "table", "drop", "alter", "begin", "commit",
    "rollback", "savepoint", "transaction", "case", "when", "then", "else",
    "end", "union", "all", "with", "over", "partition", "window", "if",
    "exists", "primary", "key", "references", "default", "check", "unique",
    "constraint", "to",
]
SQL_FUNCTIONS = [
    "count", "sum", "avg", "min", "max", "round", "upper", "lower", "substr",
    "length", "coalesce", "abs", "row_number", "rank", "dense_rank", "lag",
    "lead", "group_concat", "replace", "trim",
]


def _fmt(color: str, bold: bool = False) -> QTextCharFormat:
    f = QTextCharFormat()
    f.setForeground(QColor(color))
    if bold:
        f.setFontWeight(QFont.Weight.Bold)
    return f


class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, document, pal: Palette):
        super().__init__(document)
        self.pal = pal
        self.known = set()  # table + column names the user might type
        self._build_rules()

    def set_known_names(self, names: set[str]) -> None:
        self.known = names
        self._build_rules()
        self.rehighlight()

    def _build_rules(self) -> None:
        rules = []
        add = rules.append
        kw = r"\b(" + "|".join(SQL_KEYWORDS) + r")\b"
        add((kw, _fmt(self.pal.syn_keyword, bold=True)))
        fn = r"\b(" + "|".join(SQL_FUNCTIONS) + r")\s*\("
        add((fn, _fmt(self.pal.syn_ident)))
        if self.known:
            names = sorted(self.known, key=len, reverse=True)
            esc = [re_escape(n) for n in names]
            add((r"\b(?:" + "|".join(esc) + r")\b", _fmt(self.pal.syn_ident)))
        add((r"'(?:[^']|'')*'", _fmt(self.pal.syn_string)))
        add((r"\b\d+(?:\.\d+)?\b", _fmt(self.pal.syn_number)))
        add((r"--[^\n]*", _fmt(self.pal.syn_comment)))
        add((r"/\*.*?\*/", _fmt(self.pal.syn_comment)))
        self.rules = rules

    def highlightBlock(self, text: str) -> None:  # noqa: N802
        for pattern, fmt in self.rules:
            rx = QRegularExpression(pattern)
            it = rx.globalMatch(text)
            idx = 0
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(0), m.capturedLength(0), fmt)


def re_escape(text: str) -> str:
    return "".join("\\" + ch if ch in ".^$*+?{}[]\\|()" else ch for ch in text)


class TerminalEditor(QPlainTextEdit):
    """A QPlainTextEdit with ghost text, green/coral typing feedback, and a
    softly blinking block cursor."""

    def __init__(self, pal: Palette, parent=None):
        super().__init__(parent)
        self.pal = pal
        self.highlighter = SqlHighlighter(self.document(), pal)
        self.ghost_sql = ""
        self.mode = "type"          # type | fill | fix | answer
        self._blink = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(560)
        self._blink_timer.timeout.connect(self._toggle_blink)
        self._blink_timer.start()
        self.setTabStopDistance(28)
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.textChanged.connect(self._refresh_typed_colour)

    # -- setup -----------------------------------------------------------
    def set_known_names(self, names: set[str]) -> None:
        self.highlighter.set_known_names(names)

    def set_ghost(self, ghost_sql: str | None, mode: str = "type") -> None:
        self.ghost_sql = ghost_sql or ""
        self.mode = mode
        if ghost_sql:
            self.setPlaceholderText("\u276f " + ghost_sql)
        else:
            self.setPlaceholderText("\u276f type your query here\u2026")
        self._refresh_typed_colour()

    def _toggle_blink(self) -> None:
        self._blink = not self._blink
        if self.hasFocus():
            self.viewport().update()

    # -- ghost colour -----------------------------------------------------
    def _refresh_typed_colour(self) -> None:
        if not self.ghost_sql or self.mode != "type":
            self.setExtraSelections([])
            return
        text = self.toPlainText().strip()
        if not text:
            self.setExtraSelections([])
            return
        expected = _normalise(self.ghost_sql)
        ok = expected.startswith(_normalise(text))
        colour = self.pal.success if ok else self.pal.accent
        sel = QTextEdit.ExtraSelection()
        sel.cursor = QTextCursor(self.document())
        sel.cursor.movePosition(QTextCursor.MoveOperation.Start)
        sel.cursor.movePosition(QTextCursor.MoveOperation.End,
                                QTextCursor.MoveMode.KeepAnchor)
        sel.format.setForeground(QColor(colour))
        self.setExtraSelections([sel])

    # -- blinking block cursor -------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        if not self.hasFocus() or not self._blink:
            return
        painter = QPainter(self.viewport())
        rect = self.cursorRect()
        painter.fillRect(rect.adjusted(0, 1, 0, -1), QColor(self.pal.accent))
        painter.end()

    def focusInEvent(self, event):  # noqa: N802
        super().focusInEvent(event)
        self.viewport().update()

    def focusOutEvent(self, event):  # noqa: N802
        super().focusOutEvent(event)
        self.viewport().update()


def _normalise(text: str) -> str:
    return " ".join(text.split()).lower()