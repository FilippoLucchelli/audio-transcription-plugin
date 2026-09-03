"""Transcription with WhisperX + speaker diarization (pyannote) and word-level alignment."""

import os
from typing import Callable, Optional

import torch
import whisperx
from huggingface_hub.errors import GatedRepoError, HfHubHTTPError
from whisperx.diarize import DiarizationPipeline

ProgressCallback = Callable[[str, float], None]


def transcribe_and_diarize(
    audio_path: str,
    model_size: str = "medium",
    language: str | None = None,
    device: str = "cpu",
    compute_type: str = "int8",
    min_speakers: int | None = None,
    max_speakers: int | None = None,
    hf_token: str | None = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> dict:
    """Runs transcription + diarization on audio_path.

    Returns the whisperx result with segments annotated per speaker
    (original pyannote labels, e.g. "SPEAKER_00").

    progress_callback, if provided, is called with (stage, percentage 0-100) for
    the stages: "load_model", "transcribe", "align", "diarize".
    """

    def report(stage: str, pct: float) -> None:
        if progress_callback:
            progress_callback(stage, pct)

    hf_token = hf_token or os.environ.get("HF_TOKEN")

    if device == "cuda" and not torch.cuda.is_available():
        print("Warning: CUDA requested but not available on this machine. Falling back to CPU.")
        device = "cpu"

    if not hf_token:
        raise ValueError(
            "Missing Hugging Face token: diarization requires a valid token "
            "(HF_TOKEN environment variable, --hf-token argument, or the webapp field)."
        )

    report("load_model", 0)
    model = whisperx.load_model(model_size, device, compute_type=compute_type)
    report("load_model", 100)

    report("transcribe", 0)
    audio = whisperx.load_audio(audio_path)
    result = model.transcribe(audio, language=language)
    report("transcribe", 100)

    report("align", 0)
    align_model, align_metadata = whisperx.load_align_model(
        language_code=result["language"], device=device
    )
    result = whisperx.align(
        result["segments"], align_model, align_metadata, audio, device
    )
    report("align", 100)

    report("diarize", 0)
    try:
        diarize_model = DiarizationPipeline(token=hf_token, device=device)
    except GatedRepoError as exc:
        raise RuntimeError(
            "Access denied to the pyannote/speaker-diarization-community-1 diarization "
            "model. Visit https://huggingface.co/pyannote/speaker-diarization-community-1, "
            "log in with the account the token belongs to, and accept the usage terms "
            "('Agree and access repository'), then retry."
        ) from exc
    except HfHubHTTPError as exc:
        raise RuntimeError(
            f"Error contacting Hugging Face (invalid token or network issue?): {exc}"
        ) from exc

    try:
        diarize_segments = diarize_model(
            audio_path,
            min_speakers=min_speakers,
            max_speakers=max_speakers,
            progress_callback=lambda pct: report("diarize", pct),
        )
    except GatedRepoError as exc:
        raise RuntimeError(
            "Access denied to a model required by the diarization pipeline. Check the "
            "original error message for the repository name and accept the usage terms "
            "on its Hugging Face page."
        ) from exc

    report("diarize", 100)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    return result
