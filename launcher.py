"""Entry point used by PyInstaller to build the standalone GRAP-SQL app."""
from sqlschool.app import main

if __name__ == "__main__":
    raise SystemExit(main())
