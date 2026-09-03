"""CLI: estrazione audio -> (opzionale) pulizia rumore -> trascrizione+diarizzazione -> export."""

import argparse
import sys
from pathlib import Path

import cache
import hardware
from audio_processing import AUDIO_EXTENSIONS, check_ffmpeg, extract_audio, denoise_audio
from transcription import transcribe_and_diarize
from exporters import export_text, export_srt, export_json

STAGE_LABELS = {
    "load_model": "Caricamento modello whisper",
    "transcribe": "Trascrizione",
    "align": "Allineamento parole",
    "diarize": "Diarizzazione speaker",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Trascrivi e diarizza (per speaker) un file audio/video."
    )
    parser.add_argument("input", help="Path al file audio o video da trascrivere")
    parser.add_argument("-o", "--output-dir", default="output", help="Cartella di output")
    parser.add_argument(
        "--model",
        default=None,
        help="Dimensione modello whisper (tiny/base/small/medium/large-v3); "
        "default: scelta automatica in base all'hardware disponibile",
    )
    parser.add_argument("--language", default=None, help="Codice lingua (es. 'it'); default: auto-detect")
    parser.add_argument(
        "--device",
        default=None,
        help="Device: 'cpu' o 'cuda'; default: scelta automatica in base all'hardware disponibile",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="Compute type whisperx (int8/float16/float32); default: scelta automatica",
    )
    parser.add_argument("--min-speakers", type=int, default=None)
    parser.add_argument("--max-speakers", type=int, default=None)
    parser.add_argument("--hf-token", default=None, help="Token Hugging Face (in alternativa alla env var HF_TOKEN)")
    parser.add_argument(
        "--denoise",
        action="store_true",
        default=False,
        help="Applica pulizia rumore aggiuntiva all'audio prima della trascrizione (default: disattivato)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Ignora la cache: rilancia sempre la pipeline anche se il risultato è già in cache",
    )
    return parser.parse_args()


def print_progress(stage: str, pct: float) -> None:
    label = STAGE_LABELS.get(stage, stage)
    end = "\n" if pct >= 100 else ""
    print(f"\r{label}: {pct:5.1f}%", end=end, flush=True)


def resolve_settings(args) -> dict:
    """Applica i valori scelti dall'utente, e per quelli omessi usa la scelta
    automatica basata sull'hardware disponibile."""
    if args.model and args.device and args.compute_type:
        return {"model": args.model, "device": args.device, "compute_type": args.compute_type}

    recommended = hardware.recommend_settings()
    resolved = {
        "model": args.model or recommended["model"],
        "device": args.device or recommended["device"],
        "compute_type": args.compute_type or recommended["compute_type"],
    }
    print(
        f"Scelta automatica ({recommended['reason']}): "
        f"model={resolved['model']} device={resolved['device']} compute_type={resolved['compute_type']}"
    )
    return resolved


def run(args) -> None:
    check_ffmpeg()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"File non trovato: {input_path}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() in AUDIO_EXTENSIONS:
        audio_path = str(input_path)
    else:
        print(f"Estrazione audio da {input_path}...")
        audio_path = extract_audio(str(input_path), str(out_dir))

    if args.denoise:
        print("Pulizia rumore in corso...")
        audio_path = denoise_audio(audio_path, str(out_dir))

    settings = resolve_settings(args)

    cache_key = cache.compute_key(
        audio_path,
        model=settings["model"],
        language=args.language,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
        denoise=args.denoise,
    )

    result = None if args.no_cache else cache.load(cache_key)
    if result is not None:
        print("Trovata trascrizione in cache: salto la pipeline.")
    else:
        result = transcribe_and_diarize(
            audio_path,
            model_size=settings["model"],
            language=args.language,
            device=settings["device"],
            compute_type=settings["compute_type"],
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
            hf_token=args.hf_token,
            progress_callback=print_progress,
        )
        cache.save(cache_key, result)

    stem = input_path.stem
    export_text(result, str(out_dir / f"{stem}.txt"))
    export_srt(result, str(out_dir / f"{stem}.srt"))
    export_json(result, str(out_dir / f"{stem}.json"))

    print(f"Fatto. Output in: {out_dir}")


def main():
    args = parse_args()
    try:
        run(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"\nErrore: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
