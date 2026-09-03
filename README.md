# audio-transcription (Claude Code plugin)

Plugin/skill for [Claude Code](https://claude.com/claude-code) that transcribes and
diarizes (identifies speakers in) audio or video files locally, using WhisperX + pyannote.
No data is sent to cloud services (aside from downloading models from Hugging Face).
Works on Windows, Linux, and macOS.

The whisper model, device, and compute type are picked automatically based on the
detected hardware (CUDA/VRAM, CPU cores, RAM) unless you specify them explicitly.
Results are cached by audio content + parameters, so asking further questions about
the same recording doesn't re-run the (expensive) pipeline.

## Installation

```
/plugin marketplace add FilippoLucchelli/audio-transcription-plugin
/plugin install audio-transcription@audio-transcription-marketplace
```

Once installed, just ask Claude to transcribe an audio or video file: the skill checks
the prerequisites first, then runs the pipeline.

## Prerequisites

Before installing the plugin, make sure you have:

### 1. Python 3.10, 3.11, or 3.12

Download from [python.org/downloads](https://www.python.org/downloads/). During
setup on Windows, check "Add python.exe to PATH". Verify with:

```bash
python --version
```

### 2. ffmpeg, available on the system PATH

- **Windows**: download a build from [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
  (e.g. the "essentials" zip from gyan.dev), extract it, and add its `bin` folder to your
  system PATH (Settings → search "environment variables" → Edit the `Path` variable).
- **macOS**: `brew install ffmpeg`
- **Linux (Debian/Ubuntu)**: `sudo apt install ffmpeg`

Verify with (open a **new** terminal after installing):

```bash
ffmpeg -version
```

### 3. A Hugging Face account and access token

1. Create an account at [huggingface.co](https://huggingface.co) if you don't have one.
2. Generate an access token (read-only is enough) at
   [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
3. Visit
   [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
   while logged in with that account, and click "Agree and access repository" to accept
   the model's usage terms (required for diarization to work).
4. Make the token available to the pipeline, in one of these ways (in order of
   convenience):

   - **Permanent environment variable** — set once at the OS level, so it's always
     available to any program, including Claude Code:
     ```bash
     # Windows (persists across terminals/reboots — restart the terminal/Claude Code after)
     setx HF_TOKEN "hf_xxx"
     # Linux/macOS — add to ~/.bashrc or ~/.zshrc, then reload the shell
     export HF_TOKEN="hf_xxx"
     ```
   - **Session-only environment variable** — set it just before launching Claude
     Code in that terminal; it only lasts for that terminal session:
     ```bash
     # Windows (PowerShell)
     $env:HF_TOKEN = "hf_xxx"
     # Linux/macOS
     export HF_TOKEN="hf_xxx"
     ```
   - **Give it to Claude directly in chat** — just tell Claude your token (e.g. "my
     HF token is hf_xxx"); the skill passes it with `--hf-token` for that single run
     only, without saving it anywhere. Repeat this each time if you don't set an
     environment variable.

   The token is never written to a config file or committed anywhere by the skill.

   **Security note**: with an environment variable, Claude never needs to see or
   handle the token's value — the pipeline process reads it directly from the OS
   environment, and `check_env.py` only checks that the variable is set, not what
   it contains. If you give the token in chat instead, Claude does see it (it has
   to, to pass it along) for that conversation, though it isn't persisted beyond
   it. If you'd rather Claude never come into contact with the token at all, use
   an environment variable.

### 4. (Optional) A CUDA-capable GPU

Not required — the pipeline runs on CPU by default. If you have an NVIDIA GPU with
CUDA installed, the skill detects it automatically and picks a larger/faster model.

---

None of the above needs to be done manually before installing the plugin itself:
once installed, ask Claude to transcribe a file — it runs `check_env.py` first and
tells you exactly which of the steps above is still missing, if any.

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
                ├── run.sh              # venv setup + run (Linux/macOS)
                └── pipeline/
                    ├── main.py
                    ├── hardware.py       # hardware detection + dynamic model selection
                    ├── cache.py          # result cache keyed by audio content + params
                    ├── audio_processing.py
                    ├── transcription.py
                    └── exporters.py
```

## Manual usage (without Claude)

```bash
cd plugins/audio-transcription/skills/audio-transcription
run.bat "path/to/file.mp4" -o output --language en    # Windows
./run.sh "path/to/file.mp4" -o output --language en   # Linux/macOS
```

Output is generated in `output/<name>.{txt,srt,json}`.

## Privacy

Make sure recording and transcribing calls complies with your company policies and
GDPR (participant consent).
