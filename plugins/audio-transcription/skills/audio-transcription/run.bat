@echo off
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: Python not found. Install it from https://www.python.org/downloads/ and make sure it's on the PATH.
    exit /b 1
)

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ERROR: ffmpeg not found. Install it from https://ffmpeg.org/download.html and make sure it's on the PATH.
    exit /b 1
)

if not exist venv (
    echo Creating the skill's virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing/updating dependencies...
pip install -r requirements.txt

python pipeline\main.py %*
