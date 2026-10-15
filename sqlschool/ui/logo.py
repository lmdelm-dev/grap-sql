"""The GRAP-SQL logo: a half pen.

The mark is a fountain-pen nib split straight down the middle - the left half
inked in the accent colour, the right half in ink-black/cream - hinting at
writing (a pen) and at a lesson only half-finished (the other half still to
come).  It is drawn at run time, so the app carries no image files and the
mark recolours itself to match whichever theme is active.
"""
from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap

from ..theme import Palette


def _pen_path(w: float, h: float) -> QPainterPath:
    """A fountain-pen silhouette: a slim body that tapers to a sharp nib."""
    path = QPainterPath()
    path.moveTo(0.34 * w, 0.09 * h)   # body top-left
    path.lineTo(0.66 * w, 0.09 * h)   # body top-right
    path.lineTo(0.66 * w, 0.56 * h)   # right shoulder
    path.lineTo(0.50 * w, 0.94 * h)   # nib tip
    path.lineTo(0.34 * w, 0.56 * h)   # left shoulder
    path.closeSubpath()
    return path


def logo_pixmap(size: int, pal: Palette) -> QPixmap:
    """Render the half-pen mark at ``size`` x ``size`` pixels."""
    size = max(8, int(size))
    px = QPixmap(size, size)
    px.fill(Qt.GlobalColor.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

    w = h = float(size)
    pen = _pen_path(w, h)

    left = QPainterPath()
    left.addRect(QRectF(0, 0, w / 2, h))
    right = QPainterPath()
    right.addRect(QRectF(w / 2, 0, w / 2, h))
    # left half inked in the accent, right half in the ink/text colour
    painter.fillPath(pen.intersected(left), QColor(pal.accent))
    painter.fillPath(pen.intersected(right), QColor(pal.text))

    # the seam between the two halves (reads as the pen's centre slit)
    seam = QPen(QColor(pal.bg), max(1.0, w * 0.05))
    seam.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(seam)
    painter.drawLine(QPointF(w / 2, 0.07 * h), QPointF(w / 2, 0.93 * h))

    # a crisp outline so it stays legible on any background
    painter.setPen(QPen(QColor(pal.border), max(1.0, w * 0.03)))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawPath(pen)

    # the little air hole near the nib
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(pal.bg))
    painter.drawEllipse(QPointF(w / 2, 0.60 * h), w * 0.055, w * 0.055)
    painter.end()
    return px


def logo_icon(pal: Palette) -> QIcon:
    """A multi-resolution QIcon of the mark, for window/taskbar use."""
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(logo_pixmap(size, pal))
    return icon


__all__ = ["logo_pixmap", "logo_icon"]
