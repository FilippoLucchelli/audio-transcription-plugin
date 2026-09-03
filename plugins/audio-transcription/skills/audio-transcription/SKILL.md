---
name: audio-transcription
description: Transcribes and diarizes (identifies speakers in) the audio of an audio or video file using the local pipeline bundled in this skill (WhisperX + pyannote). Use this skill whenever the user has an audio/video file (recording, call, meeting, podcast — e.g. Teams) and wants to know what it contains or what was said, even if they don't use words like "transcribe": this also covers requests like "listen to this video", "what is it about", "summarize the audio/call", "what is said in this file", "who talked the most/how much", "subtitle this", "extract the text". In all these cases the skill first generates the transcript with speakers, then answers the specific question.
---

# Audio Transcription

Self-contained: bundles the pipeline, dependencies, and setup scripts — no
external repo needed. Run all commands from this skill's own folder.

## 1. Check prerequisites

```bash
python check_env.py
```
Exit 0 → continue. Exit 1 → **do not run the pipeline**; report the printed
problems/fixes verbatim and wait, unless told to proceed anyway.

## 2. Run

```bash
run.bat "<file or folder>" -o output --model medium --language en   # Windows
./run.sh "<file or folder>" -o output --model medium --language en  # Linux/macOS
```
(or `python pipeline\main.py ...` with the skill's venv already active)

- `input` may be a single file or a folder — a folder processes every
  audio/video file inside it and reports a per-file summary.
- Omit `--model`/`--device`/`--compute-type` unless the user asks for a
  specific one: they're auto-picked from hardware + language (non-English
  never gets less than `small`). A time estimate is printed before the run.
- Other flags, set only when relevant: `--language` (omit for auto-detect),
  `--min-speakers`/`--max-speakers` (if known), `--denoise` (only if audio is
  noisy and transcription comes out poor), `--hf-token` (see below),
  `--no-cache` (force a fresh run, ignoring any cached result).

**Hugging Face token**, if `check_env.py` flags `HF_TOKEN` missing — three
ways, user's choice: (1) permanent env var (`setx HF_TOKEN "hf_xxx"` on
Windows, or added to `~/.bashrc`/`~/.zshrc`); (2) session-only env var, set
before launching Claude Code; (3) given directly in chat — then pass it with
`--hf-token` for that one run only, **never save it anywhere**.

**Cache**: results are cached under `.cache/` by audio content + parameters,
self-pruning (30-day TTL / 2GB budget, env-configurable) — never read/edit it
by hand. A second run on the same file+params is near-instant.

## 3. Report the result

Read `output/<file_name>.txt` (or the given `-o`) and answer the user's
question, keeping speaker tags and timestamps. `.srt`/`.json` are also
generated if needed.

**Quality check** (the pipeline runs none automatically — this is your call):
if the transcript looks garbled/repetitive/incoherent, tell the user why and
ask if they want to retry with a bigger model — never automatically, since
larger models can be much slower, especially on CPU. If they agree, re-run
with `--no-cache` plus the bigger `--model`.

## Errors

Report `pipeline/main.py` failures verbatim with the corrective action.
Don't work around the pipeline (no alternative packages, no disabling
diarization unless asked).
