@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERRORE: Python non trovato. Installalo da https://www.python.org/downloads/ e assicurati che sia nel PATH.
    exit /b 1
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ERRORE: ffmpeg non trovato. Installalo da https://ffmpeg.org/download.html e assicurati che sia nel PATH.
    exit /b 1
)

if not exist venv (
    echo Creazione ambiente virtuale della skill...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installazione/aggiornamento dipendenze...
pip install -r requirements.txt

python pipeline\main.py %*
