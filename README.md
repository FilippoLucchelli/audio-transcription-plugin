# audio-transcription (Claude Code plugin)

Plugin/skill for [Claude Code](https://claude.com/claude-code) that transcribes and
diarizes (identifies speakers in) audio or video files locally, using WhisperX + pyannote.
No data is sent to cloud services (aside from downloading models from Hugging Face).

## Installation

```
/plugin marketplace add FilippoLucchelli/audio-transcription-plugin
/plugin install audio-transcription@audio-transcription-marketplace
```

Once installed, just ask Claude to transcribe an audio or video file: the skill checks
the prerequisites first, then runs the pipeline.

## Prerequisites

- Python 3.10, 3.11, or 3.12
- [ffmpeg](https://ffmpeg.org/download.html) installed and available on the system PATH
- A Hugging Face token (`HF_TOKEN` environment variable or `--hf-token` argument), with the
  usage terms of the
  [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
  model accepted

If anything is missing, the skill reports it with the exact steps to fix it (no partial
execution or workarounds).

## Structure

```
audio-transcription-plugin/
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
    └── audio-transcription/
        ├── .claude-plugin/
        │   └── plugin.json
        └── skills/
            └── audio-transcription/
                ├── SKILL.md           # instructions for the agent
                ├── check_env.py       # prerequisite checker
                ├── requirements.txt   # pipeline dependencies
                ├── run.bat             # venv setup + run (Windows)
                └── pipeline/
                    ├── main.py
                    ├── audio_processing.py
                    ├── transcription.py
                    └── exporters.py
```

## Manual usage (without Claude)

```bash
cd plugins/audio-transcription/skills/audio-transcription
run.bat "path/to/file.mp4" -o output --model medium --language en
```

Output is generated in `output/<name>.{txt,srt,json}`.

## Privacy

Make sure recording and transcribing calls complies with your company policies and
GDPR (participant consent).
