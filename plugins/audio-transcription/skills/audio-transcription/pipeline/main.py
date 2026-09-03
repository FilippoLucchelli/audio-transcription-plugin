"""CLI: audio extraction -> (optional) noise reduction -> transcription+diarization -> export."""

import argparse
import sys
from pathlib import Path

import cache
import hardware
from audio_processing import AUDIO_EXTENSIONS, check_ffmpeg, extract_audio, denoise_audio
from transcription import transcribe_and_diarize
from exporters import export_text, export_srt, export_json

STAGE_LABELS = {
    "load_model": "Loading whisper model",
    "transcribe": "Transcribing",
    "align": "Aligning words",
    "diarize": "Diarizing speakers",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Transcribe and diarize (per speaker) an audio/video file."
    )
    parser.add_argument("input", help="Path to the audio or video file to transcribe")
    parser.add_argument("-o", "--output-dir", default="output", help="Output folder")
    parser.add_argument(
        "--model",
        default=None,
        help="Whisper model size (tiny/base/small/medium/large-v3); "
        "default: automatic choice based on available hardware",
    )
    parser.add_argument("--language", default=None, help="Language code (e.g. 'en'); default: auto-detect")
    parser.add_argument(
        "--device",
        default=None,
        help="Device: 'cpu' or 'cuda'; default: automatic choice based on available hardware",
    )
    parser.add_argument(
        "--compute-type",
        default=None,
        help="whisperx compute type (int8/float16/float32); default: automatic choice",
    )
    parser.add_argument("--min-speakers", type=int, default=None)
    parser.add_argument("--max-speakers", type=int, default=None)
    parser.add_argument("--hf-token", default=None, help="Hugging Face token (alternative to the HF_TOKEN env var)")
    parser.add_argument(
        "--denoise",
        action="store_true",
        default=False,
        help="Apply extra noise reduction to the audio before transcription (default: disabled)",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=False,
        help="Ignore the cache: always re-run the pipeline even if the result is already cached",
    )
    return parser.parse_args()


def print_progress(stage: str, pct: float) -> None:
    label = STAGE_LABELS.get(stage, stage)
    end = "\n" if pct >= 100 else ""
    print(f"\r{label}: {pct:5.1f}%", end=end, flush=True)


def resolve_settings(args) -> dict:
    """Applies the values chosen by the user, and for the ones left unset uses
    the automatic choice based on the available hardware."""
    if args.model and args.device and args.compute_type:
        return {"model": args.model, "device": args.device, "compute_type": args.compute_type}

    recommended = hardware.recommend_settings()
    resolved = {
        "model": args.model or recommended["model"],
        "device": args.device or recommended["device"],
        "compute_type": args.compute_type or recommended["compute_type"],
    }
    print(
        f"Automatic choice ({recommended['reason']}): "
        f"model={resolved['model']} device={resolved['device']} compute_type={resolved['compute_type']}"
    )
    return resolved


def run(args) -> None:
    check_ffmpeg()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {input_path}")

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if input_path.suffix.lower() in AUDIO_EXTENSIONS:
        audio_path = str(input_path)
    else:
        print(f"Extracting audio from {input_path}...")
        audio_path = extract_audio(str(input_path), str(out_dir))

    if args.denoise:
        print("Running noise reduction...")
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
        print("Found cached transcription: skipping the pipeline.")
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

    print(f"Done. Output in: {out_dir}")


def main():
    args = parse_args()
    try:
        run(args)
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"\nError: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
