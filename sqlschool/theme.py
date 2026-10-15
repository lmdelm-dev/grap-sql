"""Theme: the "chill Claude-terminal" look.

Two palettes ship with the app: a warm dark one (default) and a light one
("paper terminal").  Everything visual reads its colours from here so the
whole app changes with a single setting.
"""
from __future__ import annotations

from dataclasses import dataclass, fields


@dataclass(frozen=True)
class Palette:
    name: str
    # surfaces
    bg: str          # window background
    panel: str       # pane background
    panel_alt: str   # editor / inset background
    border: str      # thin separators
    text: str        # main off-white / off-black
    muted: str       # secondary grey
    accent: str      # coral / terracotta
    accent_dim: str  # accent used for faint lines
    success: str
    hint: str
    error: str
    # syntax highlighting
    syn_keyword: str
    syn_ident: str
    syn_string: str
    syn_number: str
    syn_comment: str


DARK = Palette(
    name="dark",
    bg="#1f1e1d",
    panel="#262624",
    panel_alt="#2e2d2b",
    border="#3a3937",
    text="#e8e6e3",
    muted="#9a9691",
    accent="#d97757",
    accent_dim="#7a4a38",
    success="#8fbf6f",
    hint="#e0b354",
    error="#d98b8b",
    syn_keyword="#d97757",
    syn_ident="#8ab4d8",
    syn_string="#a3b57a",
    syn_number="#d8c07f",
    syn_comment="#6f6b66",
)

LIGHT = Palette(
    name="light",
    bg="#f3efe7",
    panel="#fbf8f1",
    panel_alt="#fffdf7",
    border="#ded5c6",
    text="#2b2a28",
    muted="#7a736a",
    accent="#c2603e",
    accent_dim="#e6c3b4",
    success="#4f7a3f",
    hint="#a9791f",
    error="#b5544f",
    syn_keyword="#b8562f",
    syn_ident="#2f6ea8",
    syn_string="#5c7a34",
    syn_number="#9a7a1f",
    syn_comment="#9a938a",
)

PALETTES = {p.name: p for p in (DARK, LIGHT)}

# Fonts -------------------------------------------------------------------
# Cascadia Code is the modern Windows terminal font; Consolas is the reliable
# fallback that ships with every Windows install.
MONO_FAMILIES = [
    "Cascadia Code",
    "Cascadia Mono",
    "Consolas",
    "JetBrains Mono",
    "Courier New",
    "monospace",
]


def mono_family() -> str:
    """Pick the nicest monospace font actually installed."""
    from PySide6.QtGui import QFontDatabase

    available = set(QFontDatabase.families())
    for fam in MONO_FAMILIES:
        if fam in available:
            return fam
    return "Courier New"


def qss(pal: Palette, font_size: int) -> str:
    """Build the global stylesheet for a palette."""
    return f"""
    QWidget {{
        background: {pal.bg};
        color: {pal.text};
        font-family: "{mono_family()}";
        font-size: {font_size}px;
    }}
    QFrame#pane {{
        background: {pal.panel};
        border: 1px solid {pal.border};
        border-radius: 8px;
    }}
    QFrame#paneActive {{
        background: {pal.panel};
        border: 1px solid {pal.accent_dim};
        border-radius: 8px;
    }}
    QLabel#paneTitle {{
        color: {pal.muted};
        font-size: {max(9, font_size - 2)}px;
        padding: 2px 2px 4px 2px;
        letter-spacing: 1px;
    }}
    QLabel#topbar, QLabel#bottombar {{
        color: {pal.muted};
        padding: 2px 8px;
    }}
    QLabel#streak {{ color: {pal.hint}; padding: 2px 8px; }}
    QLabel#lessonName {{ color: {pal.text}; padding: 2px 8px; font-weight: bold; }}
    QPushButton {{
        background: {pal.panel_alt};
        color: {pal.text};
        border: 1px solid {pal.border};
        border-radius: 6px;
        padding: 5px 12px;
    }}
    QPushButton:hover {{ border-color: {pal.accent}; color: {pal.accent}; }}
    QPushButton:pressed {{ background: {pal.panel}; }}
    QPushButton:disabled {{ color: {pal.muted}; border-color: {pal.border}; }}
    QPushButton#primary {{
        background: {pal.accent}; color: #1f1e1d; border: none; font-weight: bold;
    }}
    QPushButton#primary:hover {{ background: {pal.accent}; color: #ffffff; }}
    QPushButton#ghost {{ background: transparent; border: none; color: {pal.muted}; }}
    QPushButton#ghost:hover {{ color: {pal.accent}; }}
    QTextEdit, QPlainTextEdit {{
        background: {pal.panel_alt};
        color: {pal.text};
        border: none;
        selection-background-color: {pal.accent_dim};
        selection-color: {pal.text};
    }}
    QLineEdit {{
        background: {pal.panel_alt};
        color: {pal.text};
        border: 1px solid {pal.border};
        border-radius: 6px;
        padding: 5px 8px;
        selection-background-color: {pal.accent_dim};
    }}
    QLineEdit:focus {{ border-color: {pal.accent}; }}
    QSplitter::handle {{ background: {pal.bg}; }}
    QSplitter::handle:horizontal {{ width: 6px; }}
    QSplitter::handle:vertical {{ height: 6px; }}
    QSplitter::handle:hover {{ background: {pal.accent_dim}; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
    QScrollBar::handle:vertical {{
        background: {pal.border}; border-radius: 5px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {pal.accent_dim}; }}
    QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; }}
    QScrollBar::handle:horizontal {{
        background: {pal.border}; border-radius: 5px; min-width: 24px;
    }}
    QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
    QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
    QHeaderView::section {{
        background: {pal.panel};
        color: {pal.muted};
        border: none;
        border-bottom: 1px solid {pal.border};
        border-right: 1px solid {pal.border};
        padding: 4px 8px;
    }}
    QTableWidget {{
        background: {pal.panel_alt};
        gridline-color: {pal.border};
        border: none;
    }}
    QTableWidget::item:selected {{ background: {pal.accent_dim}; color: {pal.text}; }}
    QMenu {{
        background: {pal.panel};
        color: {pal.text};
        border: 1px solid {pal.border};
        padding: 4px;
    }}
    QMenu::item {{ padding: 6px 18px; border-radius: 4px; }}
    QMenu::item:selected {{ background: {pal.accent_dim}; color: {pal.text}; }}
    QToolTip {{
        background: {pal.panel};
        color: {pal.text};
        border: 1px solid {pal.accent};
        padding: 4px;
    }}
    QDialog {{ background: {pal.bg}; }}
    QCheckBox, QRadioButton {{ spacing: 8px; padding: 3px; }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 14px; height: 14px;
        border: 1px solid {pal.border}; border-radius: 3px;
        background: {pal.panel_alt};
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background: {pal.accent}; border-color: {pal.accent};
    }}
    QComboBox {{
        background: {pal.panel_alt}; color: {pal.text};
        border: 1px solid {pal.border}; border-radius: 6px; padding: 4px 8px;
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox QAbstractItemView {{
        background: {pal.panel}; color: {pal.text};
        selection-background-color: {pal.accent_dim};
    }}
    QSlider::groove:horizontal {{
        height: 4px; background: {pal.border}; border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {pal.accent}; width: 12px; margin: -5px 0; border-radius: 6px;
    }}
    QProgressBar {{
        background: {pal.panel_alt};
        border: 1px solid {pal.border};
        border-radius: 7px;
        text-align: center;
        color: {pal.muted};
        font-size: {max(8, font_size - 3)}px;
        max-height: 15px;
        min-height: 15px;
    }}
    QProgressBar::chunk {{
        background: {pal.accent};
        border-radius: 6px;
    }}
    QListWidget {{
        background: {pal.panel};
        border: 1px solid {pal.border};
        border-radius: 8px;
        padding: 4px;
        outline: none;
    }}
    QListWidget::item {{
        padding: 7px 10px;
        border-radius: 5px;
        color: {pal.text};
    }}
    QListWidget::item:hover {{ background: {pal.panel_alt}; }}
    QListWidget::item:selected {{ background: {pal.accent_dim}; color: {pal.text}; }}
    QListWidget::item:disabled {{ color: {pal.muted}; padding-top: 10px; }}
    QTabWidget::pane {{ border: 1px solid {pal.border}; border-radius: 6px; }}
    QTabBar::tab {{
        background: {pal.panel}; color: {pal.muted};
        padding: 6px 14px; border: 1px solid {pal.border};
        border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;
    }}
    QTabBar::tab:selected {{ color: {pal.accent}; background: {pal.panel_alt}; }}
    """
