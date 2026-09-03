#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PYTHON_BIN="python3"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN="python"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python not found. Install it from https://www.python.org/downloads/ and make sure it's on the PATH." >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ERROR: ffmpeg not found. Install it from https://ffmpeg.org/download.html and make sure it's on the PATH." >&2
    exit 1
fi

if [ ! -d venv ]; then
    echo "Creating the skill's virtual environment..."
    "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt

python pipeline/main.py "$@"
