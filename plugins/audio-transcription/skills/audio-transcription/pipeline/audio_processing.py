"""Audio extraction from video/audio files and optional noise reduction."""

import shutil
import subprocess
from pathlib import Path

import noisereduce as nr
import soundfile as sf

TARGET_SAMPLE_RATE = 16000

AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}


def check_ffmpeg() -> None:
    """Checks that ffmpeg is installed and on the PATH, otherwise raises a clear error."""
    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg not found on the system PATH. Install it from https://ffmpeg.org/download.html "
            "and make sure the 'ffmpeg' command is reachable from a terminal."
        )


def extract_audio(input_path: str, output_dir: str) -> str:
    """Converts input_path to a mono 16kHz .wav inside output_dir and returns its path."""
    check_ffmpeg()

    input_file = Path(input_path)
    if not input_file.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

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
        raise RuntimeError(f"ffmpeg failed to convert {input_path}:\n{result.stderr}")

    return str(output_path)


def denoise_audio(audio_path: str, output_dir: str) -> str:
    """Applies noise reduction to the audio file and returns the path of the cleaned file.

    Disabled by default in the pipeline: only use it if the transcription
    comes out poor for very noisy audio.
    """
    audio_file = Path(audio_path)
    data, sample_rate = sf.read(audio_path)

    reduced = nr.reduce_noise(y=data, sr=sample_rate)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / f"{audio_file.stem}_denoised.wav"

    sf.write(str(output_path), reduced, sample_rate)
    return str(output_path)
