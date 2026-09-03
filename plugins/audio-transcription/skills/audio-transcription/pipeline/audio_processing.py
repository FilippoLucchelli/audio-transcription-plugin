"""Estrazione audio da video/audio e pulizia opzionale dal rumore."""

import shutil
import subprocess
from pathlib import Path

import noisereduce as nr
import soundfile as sf

TARGET_SAMPLE_RATE = 16000

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}


def check_ffmpeg() -> None:
    """Verifica che ffmpeg sia installato e nel PATH, altrimenti solleva un errore chiaro."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg non trovato nel PATH di sistema. Installalo da https://ffmpeg.org/download.html "
            "e assicurati che il comando 'ffmpeg' sia raggiungibile da terminale."
        )


def extract_audio(input_path: str, output_dir: str) -> str:
    """Converte input_path in un .wav mono a 16kHz dentro output_dir e ne ritorna il path."""
    check_ffmpeg()

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"File non trovato: {input_path}")

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{input_file.stem}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(input_file),
        "-ac", "1",
        "-ar", str(TARGET_SAMPLE_RATE),
        "-vn",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg ha fallito la conversione di {input_path}:\n{result.stderr}")

    return str(output_path)


def denoise_audio(audio_path: str, output_dir: str) -> str:
    """Applica noise reduction al file audio e ritorna il path del file pulito.

    Disattivato di default nella pipeline: da usare solo se la trascrizione
    risulta scarsa per audio molto rumoroso.
    """
    audio_file = Path(audio_path)
    data, sample_rate = sf.read(audio_path)

    reduced = nr.reduce_noise(y=data, sr=sample_rate)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{audio_file.stem}_denoised.wav"

    sf.write(str(output_path), reduced, sample_rate)
    return str(output_path)
