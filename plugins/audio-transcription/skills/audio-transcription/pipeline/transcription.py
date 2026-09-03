"""Trascrizione con WhisperX + diarizzazione speaker (pyannote) e allineamento parola-per-parola."""

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
    """Esegue trascrizione + diarizzazione su audio_path.

    Ritorna il risultato whisperx con i segmenti annotati per speaker
    (label pyannote originali, es. "SPEAKER_00").

    progress_callback, se fornito, viene chiamato con (stage, percentuale 0-100) per le fasi:
    "load_model", "transcribe", "align", "diarize".
    """

    def report(stage: str, pct: float) -> None:
        if progress_callback:
            progress_callback(stage, pct)

    hf_token = hf_token or os.environ.get("HF_TOKEN")

    if device == "cuda" and not torch.cuda.is_available():
        print("Attenzione: CUDA richiesta ma non disponibile su questa macchina. Uso la CPU.")
        device = "cpu"

    if not hf_token:
        raise ValueError(
            "Token Hugging Face mancante: la diarizzazione richiede un token valido "
            "(variabile d'ambiente HF_TOKEN o parametro --hf-token / campo nella webapp)."
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
            "Accesso negato al modello di diarizzazione pyannote/speaker-diarization-community-1. "
            "Visita https://huggingface.co/pyannote/speaker-diarization-community-1, accedi con "
            "l'account a cui appartiene il token e accetta le condizioni d'uso ('Agree and access "
            "repository'), poi riprova."
        ) from exc
    except HfHubHTTPError as exc:
        raise RuntimeError(
            f"Errore nel contattare Hugging Face (token non valido o problema di rete?): {exc}"
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
            "Accesso negato a un modello richiesto dalla pipeline di diarizzazione. Controlla il "
            "messaggio d'errore originale per il nome del repository e accetta le condizioni d'uso "
            "sulla relativa pagina Hugging Face."
        ) from exc

    report("diarize", 100)

    result = whisperx.assign_word_speakers(diarize_segments, result)
    return result
