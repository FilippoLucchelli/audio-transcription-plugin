#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

PYTHON_BIN="python3"
command -v "$PYTHON_BIN" >/dev/null 2>&1 || PYTHON_BIN="python"

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERRORE: Python non trovato. Installalo da https://www.python.org/downloads/ e assicurati che sia nel PATH." >&2
    exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "ERRORE: ffmpeg non trovato. Installalo da https://ffmpeg.org/download.html e assicurati che sia nel PATH." >&2
    exit 1
fi

if [ ! -d venv ]; then
    echo "Creazione ambiente virtuale della skill..."
    "$PYTHON_BIN" -m venv venv
fi

source venv/bin/activate

echo "Installazione/aggiornamento dipendenze..."
pip install -r requirements.txt

python pipeline/main.py "$@"
