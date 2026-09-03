"""Export of the speaker-annotated transcription to text, SRT, and JSON formats."""

import json
from pathlib import Path


def _format_srt_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")


def export_text(result: dict, output_path: str) -> None:
    lines = []
    for segment in result.get("segments", []):
        speaker = segment.get("speaker", "unknown")
        start = segment.get("start", 0.0)
        minutes, seconds = divmod(int(start), 60)
        hours, minutes = divmod(minutes, 60)
        timestamp = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        text = segment.get("text", "").strip()
        lines.append(f"[{timestamp}] {speaker}: {text}")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def export_srt(result: dict, output_path: str) -> None:
    lines = []
    for i, segment in enumerate(result.get("segments", []), start=1):
        speaker = segment.get("speaker", "unknown")
        start = _format_srt_timestamp(segment.get("start", 0.0))
        end = _format_srt_timestamp(segment.get("end", 0.0))
        text = segment.get("text", "").strip()
        lines.append(str(i))
        lines.append(f"{start} --> {end}")
        lines.append(f"{speaker}: {text}")
        lines.append("")

    Path(output_path).write_text("\n".join(lines), encoding="utf-8")


def export_json(result: dict, output_path: str) -> None:
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
