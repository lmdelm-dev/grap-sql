# PyInstaller spec for GRAP-SQL - builds a standalone Windows app.
# Usage:  build_exe.bat   (or:  pyinstaller --noconfirm --clean GRAP-SQL.spec)
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules("sqlglot")

a = Analysis(
    ["launcher.py"],
    pathex=["."],
    binaries=[],
    datas=[("data", "data")],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pytestqt"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GRAP-SQL",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,            # no black window for the learner
    disable_windowed_traceback=False,
    icon="assets/grap_sql.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GRAP-SQL",
)
