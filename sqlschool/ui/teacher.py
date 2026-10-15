"""The Teacher pane (left): calm explanations, typed out line by line.

* text appears gently, line by line (skippable by clicking or any key)
* underlined words are clickable - a one-line plain-English definition pops up
* a "Slow down" control re-explains the same idea even more simply
"""
from __future__ import annotations

import re

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QColor, QCursor, QTextCursor
from PySide6.QtWidgets import QPushButton, QTextBrowser, QToolTip

from ..theme import Palette
from .widgets import PaneFrame

# ~word~(one-line definition)   ->  clickable glossary term
GLOSS = re.compile(r"~([^~]+)~\(([^)]{1,160})\)")


class TeacherPane(PaneFrame):
    slow_down_requested = Signal()

    def __init__(self, pal: Palette, parent=None):
        super().__init__("1 · Teacher", pal, parent)
        self.pal = pal
        self.current_fragments: list[tuple[str, str]] = []
        self.revealed = 0
        self._timer = QTimer(self)
        self._timer.setInterval(120)
        self._timer.timeout.connect(self._reveal_one)
        self.definitions: dict[str, str] = {}

        slow = QPushButton("🐢 Slow down")
        slow.setObjectName("ghost")
        slow.setToolTip("Repeat this explanation more simply.")
        slow.clicked.connect(self.slow_down_clicked)
        self.slow_button = slow
        self.add_head_widget(slow)

        self.browser = QTextBrowser()
        self.browser.setObjectName("pane")
        self.browser.setOpenLinks(False)
        self.browser.anchorClicked.connect(self._anchor_clicked)
        self.browser.document().setDefaultStyleSheet(_teacher_css(pal))
        self.browser.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.body.addWidget(self.browser, 1)
        self.sync_theme()

    def sync_theme(self) -> None:
        self.browser.document().setDefaultStyleSheet(_teacher_css(self.pal))

    # -- content ----------------------------------------------------------
    def show_fragments(self, fragments: list[tuple[str, str]]) -> None:
        """fragments: list of (kind, text). kinds: prompt|real|task|trick|line|err|sql"""
        self.current_fragments = fragments
        self.definitions = {}
        self.revealed = 0
        self.browser.clear()
        if not fragments:
            return
        self._render_preview()
        self._timer.start()

    def _render_preview(self) -> None:
        """Show a dim skeleton of the upcoming lines (and the thinking sparkle)."""
        html = [_fragment_html(k, t, self.pal, collect=self.definitions)
                for k, t in self.current_fragments]
        preview = "".join(
            h for h in html[: max(0, self.revealed)]) 
        if self.revealed < len(self.current_fragments):
            preview += '<span class="think">\u273b</span>'
        self.browser.setHtml(preview)

    def _reveal_one(self) -> None:
        self.revealed += 1
        done = self.revealed >= len(self.current_fragments)
        self._render_preview()
        if done:
            self._timer.stop()

    def skip_typing(self) -> None:
        if self._timer.isActive():
            self.revealed = len(self.current_fragments)
            self._render_preview()
            self._timer.stop()

    # -- interactions ------------------------------------------------------
    def mousePressEvent(self, event):  # noqa: N802
        self.skip_typing()
        super().mousePressEvent(event)

    def keyPressEvent(self, event):  # noqa: N802
        self.skip_typing()
        super().keyPressEvent(event)

    def _anchor_clicked(self, url) -> None:
        word = url.toString()
        if word.startswith("g:"):
            term = word[2:]
            definition = self.definitions.get(term, "")
            if definition:
                QToolTip.showText(QCursor.pos(), "<b>%s</b> — %s" % (term, definition),
                                  self.browser)

    def slow_down_clicked(self, *_args) -> None:
        self.slow_down_requested.emit()


def _fragment_html(kind: str, text: str, pal: Palette, collect: dict) -> str:
    if kind == "sql":
        text = "<code style='color:%s;'>%s</code>" % (pal.syn_keyword, _esc(text))
        return '<div class="block">%s</div>' % text
    if kind == "task":
        return ('<div class="task"><span style="color:%s;">→ Try typing:</span> %s</div>'
                % (pal.accent, _esc(text)))
    if kind == "trick":
        return '<div class="trick"><span class="think">✻</span> %s</div>' % _esc(text)
    if kind == "real":
        return '<div class="real">◈ Real life: %s</div>' % _esc(text)
    if kind == "err":
        return '<div class="err">%s</div>' % _esc(text)
    if kind == "ok":
        return '<div class="ok">%s</div>' % _esc(text)
    if kind in ("line", "prompt"):
        return '<div class="p">%s</div>' % _gloss_html(_esc(text), collect)
    return '<div class="p">%s</div>' % _esc(text)


def _gloss_html(text: str, collect: dict) -> str:
    def replace(m: re.Match) -> str:
        word = m.group(1)
        definition = m.group(2)
        collect[word] = definition
        return '<a href="g:%s" title="%s">%s</a>' % (word, word, word)
    return GLOSS.sub(replace, text)


def _esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def _teacher_css(pal: Palette) -> str:
    return """
    QTextBrowser { background: %s; border: none; padding: 6px; }
    div.p { margin: 2px 0 7px 0; line-height: 1.45; }
    div.real { margin: 4px 0 8px 0; color: %s; }
    div.task { margin: 6px 0 8px 0; color: %s; font-weight: bold; }
    div.trick { margin: 6px 0 2px 0; color: %s; }
    div.block { margin: 5px 0; padding: 5px 8px; background:%s; border-radius:6px; }
    div.err { color: %s; margin: 4px 0; }
    div.ok { color: %s; margin: 4px 0; }
    span.think { color: %s; }
    a { color: %s; text-decoration: underline; }
    """ % (pal.panel, pal.accent, pal.text, pal.hint, pal.panel_alt,
           pal.error, pal.success, pal.muted, pal.accent)