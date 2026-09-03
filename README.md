# audio-transcription (Claude Code plugin)

Plugin/skill per [Claude Code](https://claude.com/claude-code) che trascrive e diarizza
(identifica gli speaker) file audio o video in locale, usando WhisperX + pyannote.
Nessun dato viene inviato a servizi cloud (a parte il download dei modelli da Hugging Face).

## Installazione

```
/plugin marketplace add FilippoLucchelli/audio-transcription-plugin
/plugin install audio-transcription@audio-transcription-marketplace
```

Dopo l'installazione, chiedi semplicemente a Claude di trascrivere un file audio o video:
la skill verifica prima i prerequisiti e poi esegue la pipeline.

## Prerequisiti

- Python 3.10, 3.11 o 3.12
- [ffmpeg](https://ffmpeg.org/download.html) installato e nel PATH di sistema
- Un token Hugging Face (variabile d'ambiente `HF_TOKEN` o parametro `--hf-token`), con le
  condizioni d'uso del modello
  [pyannote/speaker-diarization-community-1](https://huggingface.co/pyannote/speaker-diarization-community-1)
  accettate

Se manca qualcosa, la skill lo segnala con i passaggi esatti per risolvere (nessuna
esecuzione parziale/workaround).

## Struttura

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
                ├── SKILL.md           # istruzioni per l'agente
                ├── check_env.py       # verifica prerequisiti
                ├── requirements.txt   # dipendenze della pipeline
                ├── run.bat             # setup venv + esecuzione (Windows)
                └── pipeline/
                    ├── main.py
                    ├── audio_processing.py
                    ├── transcription.py
                    └── exporters.py
```

## Uso manuale (senza Claude)

```bash
cd plugins/audio-transcription/skills/audio-transcription
run.bat "path/al/file.mp4" -o output --model medium --language it
```

Output generato in `output/<nome>.{txt,srt,json}`.

## Privacy

Verifica che la registrazione e la trascrizione delle chiamate sia conforme alle policy
aziendali e al GDPR (consenso dei partecipanti).
