---
name: audio-transcription
description: Transcribes and diarizes (identifies speakers in) the audio of an audio or video file using the local pipeline bundled in this skill (WhisperX + pyannote). Use this skill whenever the user has an audio/video file (recording, call, meeting, podcast — e.g. Teams) and wants to know what it contains or what was said, even if they don't use words like "transcribe": this also covers requests like "listen to this video", "what is it about", "summarize the audio/call", "what is said in this file", "who talked the most/how much", "subtitle this", "extract the text". In all these cases the skill first generates the transcript with speakers, then answers the specific question.
---

# Audio Transcription

Self-contained skill: it bundles the full pipeline (`pipeline/`), its dependencies
(`requirements.txt`), and a setup script (`run.bat`/`run.sh`). It does not depend on
any other repo or external folder: you can copy the entire skill folder to another
machine and it works the same way.

All commands below must be run from the skill's own folder
(`.claude/skills/audio-transcription/`).

## Step 1 — Check prerequisites

Before running any transcription, run:

```bash
python check_env.py
```

- If it exits with code 0 → proceed to Step 2.
- If it exits with code 1 → **do not attempt to run the pipeline**. Report to the
  user, verbatim, the list of problems and fixes printed by the script (Python
  version, ffmpeg, venv/dependencies, Hugging Face token). Stop and wait for the
  user to fix them, unless they explicitly ask you to proceed anyway.

## Step 2 — Run the transcription

Without managing the venv/dependencies by hand (`run.bat`/`run.sh` create the
skill's venv and install `requirements.txt` on first run):

```bash
run.bat "<path to audio or video file>" -o output --model medium --language en   # Windows
./run.sh "<path to audio or video file>" -o output --model medium --language en  # Linux/macOS
```

Or, with the skill's venv already active (`venv\Scripts\activate` on Windows,
`source venv/bin/activate` on Linux/macOS):

```bash
python pipeline\main.py "<path to audio or video file>" -o output --model medium --language en
```

If you don't specify `--model`/`--device`/`--compute-type`, the pipeline picks
them automatically based on the detected hardware (`pipeline/hardware.py`:
available GPU/VRAM, CPU cores, RAM) and the target `--language` — non-English
languages are never given a model smaller than `small`, since `tiny`/`base`
are unreliable outside English — and prints the choice with its reasoning.
Leave these parameters unset unless the user explicitly asks for a specific
model or device.

Before actually running, the pipeline prints a rough estimate of the audio
duration and expected processing time (based on the chosen model/device); it's
a ballpark figure, not a guarantee, useful to warn the user before a
potentially long run (e.g. `large-v3` on CPU).

### Batch mode

`input` can also be a folder instead of a single file: the pipeline processes
every audio/video file inside it (one at a time, same parameters for all) and
reports a per-file summary at the end, continuing past individual failures
rather than stopping the whole batch. Use this when the user has several
recordings to transcribe in one go (e.g. "transcribe all the calls in this
folder").

Adjust the other parameters based on the user's request:

| Parameter | When to use it |
|---|---|
| `--model` | Only if the user explicitly asks for a model size (`tiny/base/small/medium/large-v3`); otherwise leave it unset (auto) |
| `--language` | Language code (e.g. `en`, `it`); omit for auto-detect |
| `--device` | Only if the user wants to force `cuda`/`cpu`; otherwise leave it unset (auto) |
| `--min-speakers` / `--max-speakers` | If the user knows how many speakers are present, this helps diarization |
| `--denoise` | Only if the audio is very noisy and the transcription comes out poor |
| `--hf-token` | Only if the user prefers to pass it by hand instead of setting `HF_TOKEN` |
| `--no-cache` | Only if the user wants to force a fresh transcription, ignoring an existing cached result |

### Hugging Face token

If `check_env.py` reports that `HF_TOKEN` is not set, the user has three ways to
provide it (in order of convenience):

1. **Permanent environment variable** — set once at the system level, always
   available: `setx HF_TOKEN "hf_xxx"` on Windows (restart the terminal
   afterwards), or add it to `~/.bashrc`/`~/.zshrc` on Linux/macOS.
2. **Environment variable for the current session only** — set in the terminal
   before launching Claude Code (`$env:HF_TOKEN=...` on PowerShell, `export
   HF_TOKEN=...` on Linux/macOS); only valid for that session.
3. **Given directly in chat** — the user writes it to you in a message; in this
   case pass it with `--hf-token` for that single run, **do not save it**
   anywhere (no config file, no cache).

## Cache

Transcription+diarization results are cached in `.cache/` (inside the skill's
folder), indexed by audio content + parameters (model, language, speakers,
denoise). If the user asks further questions about the same recording (even
in a different session), there's no need to re-run the pipeline: a second run
on the same file with the same parameters will automatically hit the cache
and return almost instantly. The cache should never be read or edited by hand.
It self-prunes (entries older than 30 days, or the oldest ones if it grows
past 2 GB — both configurable via `AUDIO_TRANSCRIPTION_CACHE_TTL_DAYS` and
`AUDIO_TRANSCRIPTION_CACHE_MAX_MB`), so it never needs manual cleanup.

## Step 3 — Report the result

Once done, the generated files are in `output/<file_name>.{txt,srt,json}`
(inside the skill's folder, unless a different `-o` was given).
Read `<file_name>.txt` and report its content to the user (or a summary, if
very long), keeping the speaker tags (`SPEAKER_00`, ...) and timestamps.

### Quality check

While reading the transcript, judge whether it actually makes sense (coherent
sentences, not garbled/repetitive/mostly empty). The pipeline does not run any
automatic quality check — this judgment call is yours. If the transcript looks
poor:

1. Tell the user it looks low-quality and why (e.g. fragmented, repetitive,
   large gaps).
2. Ask if they want to retry with a bigger model (e.g. `--model medium` or
   `--model large-v3` if hardware allows) — **don't retry automatically**: a
   larger model can take much longer, especially on CPU, so it's the user's
   call whether that trade-off is worth it.
3. If they agree, re-run with `--no-cache` (otherwise the cached low-quality
   result would just be returned again) and the larger `--model`.

## Errors during execution

If `pipeline/main.py` fails with an error (e.g. file not found, ffmpeg failed,
diarization model access not granted on Hugging Face), report the exact error
message to the user along with the corrective action, without attempting
workarounds that bypass the pipeline (e.g. don't install alternative packages,
don't disable diarization unless asked to).

## Skill structure

```
audio-transcription/
├── SKILL.md
├── check_env.py         # checks prerequisites, tells you how to fix them
├── requirements.txt     # pipeline's Python dependencies
├── run.bat               # creates venv, installs dependencies, runs the pipeline (Windows)
├── run.sh                # run.bat equivalent for Linux/macOS
└── pipeline/
    ├── main.py            # CLI entry point
    ├── hardware.py          # hardware detection + dynamic model selection
    ├── cache.py              # result cache keyed by file + parameters
    ├── audio_processing.py  # audio extraction, duration probing, optional noise reduction
    ├── transcription.py     # WhisperX transcription + pyannote diarization
    └── exporters.py          # export to txt / srt / json
```
