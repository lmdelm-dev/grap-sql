"""A 30-second first-run welcome.

"Hi! Type your name… we'll start from zero." No signup, no internet, no
configuration.  The welcome is only shown once; afterwards the app goes
straight into Lesson 1.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from .. import APP_NAME
from .logo import logo_pixmap


class WelcomeDialog(QDialog):
    def __init__(self, pal, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        header = QHBoxLayout()
        mark = QLabel()
        mark.setPixmap(logo_pixmap(44, pal))
        mark.setFixedSize(44, 44)
        mark.setScaledContents(True)
        header.addWidget(mark)
        title = QLabel("<span style='font-size:15pt;'>%s</span>" % APP_NAME)
        header.addWidget(title)
        header.addStretch(1)
        lay.addLayout(header)

        intro = QLabel(
            "Hi there, and welcome!\n"
            "We're going to learn the language of databases together - you and "
            "me - starting from <b>absolute zero</b>.\n"
            "No experience needed. No tricky words without an explanation. "
            "You'll be typing real SQL in about three minutes.\n\n"
            "What should I call you?")
        intro.setWordWrap(True)
        lay.addWidget(intro)

        row = QHBoxLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("your name")
        self.name.setMaxLength(24)
        row.addWidget(self.name, 1)
        start = QPushButton("Let's begin ✻")
        start.setObjectName("primary")
        start.clicked.connect(self.accept)
        row.addWidget(start)
        lay.addLayout(row)

        small = QLabel("Your name only gets saved on this computer. "
                       "Everything runs offline.")
        small.setStyleSheet("color:%s; font-size:9pt;" % pal.muted)
        small.setWordWrap(True)
        lay.addWidget(small)

        self.name.returnPressed.connect(self.accept)

    @property
    def learner_name(self) -> str:
        name = self.name.text().strip()
        return name or "friend"