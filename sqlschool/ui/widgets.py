"""Small shared UI pieces: pane frames, result tables, status lines."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class PaneFrame(QFrame):
    """A rounded pane with a slim title and an active glow."""

    def __init__(self, title: str, pal, parent=None):
        super().__init__(parent)
        self._pal = pal
        self.setObjectName("pane")
        self.outline = QVBoxLayout(self)
        self.outline.setContentsMargins(10, 6, 10, 8)
        self.outline.setSpacing(4)
        header = QHBoxLayout()
        header.setSpacing(6)
        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("paneTitle")
        header.addWidget(title_lbl)
        header.addStretch(1)
        self.head_widgets = []
        self.outline.addLayout(header)
        self.body = QVBoxLayout()
        self.body.setContentsMargins(2, 2, 2, 2)
        self.body.setSpacing(4)
        self.outline.addLayout(self.body, 1)

    def add_head_widget(self, widget: QWidget) -> None:
        box = self.outline.itemAt(0)  # header layout
        box.addWidget(widget)          # noqa: SLF001
        self.head_widgets.append(widget)

    def set_active(self, active: bool) -> None:
        self.setObjectName("paneActive" if active else "pane")
        style = self.style()
        style.unpolish(self)
        style.polish(self)

    def add(self, widget: QWidget) -> None:
        self.body.addWidget(widget)

    def layout_for_add(self) -> QVBoxLayout:
        return self.body


class ResultTable(QTableWidget):
    """A results grid with a friendly row count label."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.verticalHeader().setVisible(False)
        self.verticalHeader().setDefaultSectionSize(24)
        self.horizontalHeader().setStretchLastSection(True)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setShowGrid(True)
        self.setAlternatingRowColors(True)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

    def show_result(self, columns: list[str], rows: list[tuple],
                    row_note: str = "", truncated: bool = False) -> None:
        self.clear()
        self.setColumnCount(len(columns))
        self.setHorizontalHeaderLabels(list(columns))
        self.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                item = QTableWidgetItem(_cell_text(val))
                align = (Qt.AlignmentFlag.AlignRight if _is_number(val)
                         else Qt.AlignmentFlag.AlignLeft)
                item.setTextAlignment(align | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(r, c, item)
        if not rows and columns:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem("—  no rows —"))
            self.setSpan(0, 0, 1, len(columns))
        else:
            self._fit_columns()

    def _fit_columns(self, cap: int = 280) -> None:
        """Size columns to their contents, but keep very wide ones readable."""
        self.resizeColumnsToContents()
        for c in range(self.columnCount() - 1):
            if self.columnWidth(c) > cap:
                self.setColumnWidth(c, cap)

    def show_status(self, text: str, colour: str | None = None) -> None:
        """Show one terminal-style line instead of a table."""
        self.clear()
        self.setColumnCount(1)
        self.setRowCount(1)
        self.setHorizontalHeaderLabels([""])
        item = QTableWidgetItem(text)
        if colour:
            item.setForeground(QColorHex(colour))
        self.setItem(0, 0, item)


def QColorHex(hexstr: str):
    from PySide6.QtGui import QColor
    return QColor(hexstr)


def _is_number(value) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)) \
        or value is None


def _cell_text(value) -> str:
    if value is None:
        return "∅"
    if isinstance(value, float):
        if value == int(value):
            return str(int(value))
        return f"{value:.2f}"
    return str(value)


def make_label(text: str, object_name: str = "", wrap: bool = True) -> QLabel:
    lbl = QLabel(text)
    lbl.setWordWrap(wrap)
    lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    if object_name:
        lbl.setObjectName(object_name)
    return lbl