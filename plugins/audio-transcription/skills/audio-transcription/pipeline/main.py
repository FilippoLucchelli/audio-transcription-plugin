"""CLI: estrazione audio -> (opzionale) pulizia rumore -> trascrizione+diarizzazione -> export."""

import argparse
import sys
from pathlib import Path

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
    parser.add_argument("--model", default="medium", help="Dimensione modello whisper (tiny/base/small/medium/large-v3)")
    parser.add_argument("--language", default=None, help="Codice lingua (es. 'it'); default: auto-detect")
    parser.add_argument("--device", default="cpu", help="Device: 'cpu' o 'cuda'")
    parser.add_argument("--compute-type", default="int8", help="Compute type whisperx (int8/float16/float32)")
    parser.add_argument("--min-speakers", type=int, default=None)
    parser.add_argument("--max-speakers", type=int, default=None)
    parser.add_argument("--hf-token", default=None, help="Token Hugging Face (in alternativa alla env var HF_TOKEN)")
    parser.add_argument(
        "--denoise",
        action="store_true",
        default=False,
        help="Applica pulizia rumore aggiuntiva all'audio prima della trascrizione (default: disattivato)",
    )
    return parser.parse_args()


def print_progress(stage: str, pct: float) -> None:
    label = STAGE_LABELS.get(stage, stage)
    end = "\n" if pct >= 100 else ""
    print(f"\r{label}: {pct:5.1f}%", end=end, flush=True)


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

    result = transcribe_and_diarize(
        audio_path,
        model_size=args.model,
        language=args.language,
        device=args.device,
        compute_type=args.compute_type,
        min_speakers=args.min_speakers,
        max_speakers=args.max_speakers,
        hf_token=args.hf_token,
        progress_callback=print_progress,
    )

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
