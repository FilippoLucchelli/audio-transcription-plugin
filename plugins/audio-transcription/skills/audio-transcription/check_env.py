"""Verifica i prerequisiti della pipeline di trascrizione/diarizzazione di questa skill.

Uso: python check_env.py   (da lanciare dalla cartella della skill, o con path assoluto)
Esce con codice 0 se tutto è pronto, 1 se manca qualcosa (e stampa i passaggi
esatti per risolvere ogni problema trovato).
"""

import importlib.util
import os
import shutil
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent

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
            f"Versione Python non supportata: {major}.{minor}",
            "Installa Python 3.10, 3.11 o 3.12 da https://www.python.org/downloads/ "
            "e ricrea il venv della skill (cancella la cartella 'venv' ed esegui di nuovo run.bat, "
            "oppure 'python -m venv venv' dentro la cartella della skill).",
        )


def check_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        fail(
            "ffmpeg non trovato nel PATH di sistema",
            "Scarica ffmpeg da https://ffmpeg.org/download.html, estrai l'eseguibile "
            "e aggiungi la cartella 'bin' al PATH di sistema. Verifica con 'ffmpeg -version' "
            "da un nuovo terminale.",
        )


def check_venv_and_packages() -> None:
    venv_dir = SKILL_ROOT / "venv"
    if not venv_dir.exists():
        fail(
            "Virtual environment della skill non trovato",
            f"Crealo con: python -m venv venv (dentro '{SKILL_ROOT}'), poi attivalo "
            "(venv\\Scripts\\activate) e installa le dipendenze con "
            "'pip install -r requirements.txt'. In alternativa lancia run.bat, "
            "che lo fa automaticamente.",
        )
        return

    missing = [pkg for pkg in REQUIRED_PACKAGES if importlib.util.find_spec(pkg) is None]
    if missing:
        fail(
            f"Dipendenze Python mancanti nell'ambiente corrente: {', '.join(missing)}",
            f"Attiva il venv della skill ('{venv_dir}\\Scripts\\activate') e installa le dipendenze "
            "con: pip install -r requirements.txt. In alternativa lancia run.bat.",
        )


def check_hf_token() -> None:
    if not os.environ.get("HF_TOKEN"):
        fail(
            "Token Hugging Face (HF_TOKEN) non impostato",
            "1) Crea un account su https://huggingface.co e genera un access token da "
            "https://huggingface.co/settings/tokens. "
            "2) Accetta le condizioni d'uso del modello "
            "https://huggingface.co/pyannote/speaker-diarization-community-1 (loggato con lo "
            "stesso account). "
            "3) Imposta la variabile d'ambiente HF_TOKEN con il token, oppure passalo con "
            "--hf-token al comando.",
        )


def main() -> int:
    check_python_version()
    check_ffmpeg()
    check_venv_and_packages()
    check_hf_token()

    if not PROBLEMS:
        print("OK: tutti i prerequisiti sono soddisfatti.")
        return 0

    print("Prerequisiti mancanti:\n")
    for i, (title, fix) in enumerate(PROBLEMS, start=1):
        print(f"{i}. {title}")
        print(f"   Come risolvere: {fix}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
