#!/usr/bin/env bash
# Build Mess Ledger into a single binary that runs anywhere Python isn't
# installed.
#
#   ./build.sh              one file  -> dist/MessLedger
#   ./build.sh --onedir     a folder -> faster to start, same result
#   ./build.sh --clean      remove build/ and dist/ and stop
#
# Needs PyInstaller once:  python3 -m pip install --user pyinstaller
# Pillow is optional: without it the art falls back to plain paper.
set -euo pipefail

cd "$(dirname "$0")"
SRC="$(pwd)"

MODE="--onefile"
[[ "${1:-}" == "--onedir" ]] && MODE="--onedir"

if [[ "${1:-}" == "--clean" ]]; then
    rm -rf build dist
    echo "removed build/ and dist/"
    exit 0
fi

if ! python3 -c "import PyInstaller" >/dev/null 2>&1; then
    cat >&2 <<'EOF'
PyInstaller is not installed.

    python3 -m pip install --user pyinstaller

then re-run this script.
EOF
    exit 1
fi

python3 - <<'PY'
try:
    import PIL  # noqa: F401
except Exception:
    print("note: Pillow not found - banners will fall back to plain paper")
PY

# art, icons, web icons and the licensed fonts all travel with the binary
SEP=":"
[[ "$MODE" == "--onedir" ]] && SEP=";"

echo "building Mess Ledger ($MODE) ..."
python3 -m PyInstaller \
    --noconfirm --clean "$MODE" \
    --name "MessLedger" \
    --windowed \
    --add-data "$SRC/art${SEP}art" \
    --add-data "$SRC/icons${SEP}icons" \
    --add-data "$SRC/web${SEP}web" \
    --add-data "$SRC/fonts${SEP}fonts" \
    --hidden-import PIL._tkinter_finder \
    meal_gui.py

cat <<EOF

built.

    ./dist/MessLedger          run it
    ./dist/MessLedger phone    serve it to your phone over Wi-Fi

Your data is never inside the binary and is not touched by deleting it:

    ~/.local/share/bhu_meal_tracker/history.json
    ~/.config/bhu_meal_tracker/config.ini

Bundled fonts are SIL OFL 1.1 (see fonts/OFL-*.txt). Install them on a
Linux desktop for the app to pick them up at runtime:

    ./install.sh --no-launch

exports land in ~/Documents/MessLedger
EOF