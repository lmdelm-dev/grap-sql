"""Render the GRAP-SQL half-pen mark to PNG + ICO files.

Used when packaging a standalone build (see ``build_exe.bat``).  The app itself
draws the mark at run time, so these files are only needed for the Windows
executable icon.

    python tools/make_icon.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QGuiApplication  # noqa: E402
from PySide6.QtGui import QImageWriter  # noqa: E402

from sqlschool.theme import DARK  # noqa: E402
from sqlschool.ui.logo import logo_pixmap  # noqa: E402


def main() -> int:
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)
    out = ROOT / "assets"
    out.mkdir(exist_ok=True)

    png = out / "grap_sql.png"
    logo_pixmap(256, DARK).save(str(png), "PNG")
    print("wrote", png)

    ico = out / "grap_sql.ico"
    image = logo_pixmap(256, DARK).toImage()
    writer = QImageWriter(str(ico), b"ico")
    if writer.write(image):
        print("wrote", ico)
    else:
        print("could not write .ico (%s); PNG is enough for the app." % writer.errorString())
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
