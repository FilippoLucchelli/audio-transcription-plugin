"""Checks the prerequisites for this skill's transcription/diarization pipeline.

Usage: python check_env.py   (run from the skill's folder, or with an absolute path)
Exits with code 0 if everything is ready, 1 if something is missing (and prints
the exact steps to fix each problem found).
"""

import importlib.util
import os
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent
IS_WINDOWS = sys.platform.startswith("win")
VENV_ACTIVATE_HINT = "venv\\Scripts\\activate" if IS_WINDOWS else "source venv/bin/activate"
RUN_SCRIPT = "run.bat" if IS_WINDOWS else "run.sh"

REQUIRED_PACKAGES = [
    "whisperx",
    "torch",
    "torchaudio",
    "noisereduce",
    "soundfile",
]

PROBLEMS = []


def fail(title: str, fix: str) -> None:
    PROBLEMS.append((title, fix))


def check_python_version() -> None:
    major, minor = sys.version_info[:2]
    if not (major == 3 and minor in (10, 11, 12)):
        fail(
            f"Unsupported Python version: {major}.{minor}",
            "Install Python 3.10, 3.11, or 3.12 from https://www.python.org/downloads/ "
            f"and recreate the skill's venv (delete the 'venv' folder and run {RUN_SCRIPT} "
            "again, or 'python -m venv venv' inside the skill's folder).",
        )


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        fail(
            "ffmpeg not found on the system PATH",
            "Download ffmpeg from https://ffmpeg.org/download.html, extract the "
            "executable, and add its 'bin' folder to the system PATH. Verify with "
            "'ffmpeg -version' in a new terminal.",
        )


def check_venv_and_packages() -> None:
    venv_dir = SKILL_ROOT / "venv"
    if not venv_dir.exists():
        fail(
            "Skill's virtual environment not found",
            f"Create it with: python -m venv venv (inside '{SKILL_ROOT}'), then activate "
            f"it ({VENV_ACTIVATE_HINT}) and install dependencies with "
            f"'pip install -r requirements.txt'. Alternatively, run {RUN_SCRIPT}, "
            "which does this automatically.",
        )
        return

    missing = [pkg for pkg in REQUIRED_PACKAGES if importlib.util.find_spec(pkg) is None]
    if missing:
        fail(
            f"Missing Python dependencies in the current environment: {', '.join(missing)}",
            f"Activate the skill's venv ({VENV_ACTIVATE_HINT}) and install dependencies "
            f"with: pip install -r requirements.txt. Alternatively, run {RUN_SCRIPT}.",
        )


def check_hf_token() -> None:
    if not os.environ.get("HF_TOKEN"):
        fail(
            "Hugging Face token (HF_TOKEN) not set",
            "1) Create an account at https://huggingface.co and generate an access token "
            "at https://huggingface.co/settings/tokens. "
            "2) Accept the usage terms of the model "
            "https://huggingface.co/pyannote/speaker-diarization-community-1 (logged in "
            "with that same account). "
            "3) Set the HF_TOKEN environment variable with the token, or pass it with "
            "--hf-token to the command.",
        )


def main() -> int:
    check_python_version()
    check_ffmpeg()
    check_venv_and_packages()
    check_hf_token()

    if not PROBLEMS:
        print("OK: all prerequisites are satisfied.")
        return 0

    print("Missing prerequisites:\n")
    for i, (title, fix) in enumerate(PROBLEMS, start=1):
        print(f"{i}. {title}")
        print(f"   How to fix it: {fix}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
