#!/usr/bin/env bash
# Build Mess Ledger into a single self-contained binary.
#
#   ./build.sh              one-file build -> dist/MessLedger
#   ./build.sh --onedir     faster to start, a folder instead of one file
#
# Needs PyInstaller once:  pip install pyinstaller
# The result runs on any machine with the same OS and arch, with no
# Python installed and no access to the source tree.
set -euo pipefail

cd "$(dirname "$0")"

if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    echo "PyInstaller is not installed."
    echo "  python3 -m pip install --user pyinstaller"
    exit 1
fi

# PIL is optional at runtime: without it the art falls back to plain
# paper, so do not fail the build if it is missing.
python3 - <<'PY'
try:
    import PIL  # noqa: F401
except Exception:
    import sys
    print("warning: Pillow not found, banners will fall back to paper")
    sys.exit(0)
PY

MODE="--onefile"
[[ "${1:-}" == "--onedir" ]] && MODE="--onedir"

echo "building Mess Ledger ($MODE) ..."
python3 -m PyInstaller \
    --noconfirm --clean $MODE \
    --name "MessLedger" \
    --windowed \
    --add-data "art:art" \
    --add-data "icons:icons" \
    --hidden-import PIL._tkinter_finder \
    meal_gui.py

echo
echo "done -> dist/MessLedger"
echo "settings and history stay in:"
echo "  ~/.config/bhu_meal_tracker/config.ini"
echo "  ~/.local/share/bhu_meal_tracker/history.json"
echo "exports land in ~/Documents/MessLedger"