---
name: audio-transcription
description: Trascrive e diarizza (identifica gli speaker) l'audio di un file audio o video usando la pipeline locale bundled in questa skill (WhisperX + pyannote). Usa questa skill quando l'utente chiede di trascrivere, sottotitolare o analizzare l'audio/il parlato di una registrazione, chiamata, video o meeting (es. Teams).
---

# Audio Transcription

Skill autonoma: contiene la pipeline completa (`pipeline/`), le sue dipendenze
(`requirements.txt`) e lo script di setup (`run.bat`). Non dipende da nessun
altro repo o cartella esterna: puoi copiare l'intera cartella della skill su
un'altra macchina e funziona allo stesso modo.

Tutti i comandi sotto vanno eseguiti dalla cartella della skill stessa
(`.claude/skills/audio-transcription/`).

## Passo 1 — Verifica prerequisiti

Prima di eseguire qualsiasi trascrizione, lancia:

```bash
python check_env.py
```

- Se esce con codice 0 → prosegui al Passo 2.
- Se esce con codice 1 → **non tentare di eseguire la pipeline**. Riporta all'utente,
  parola per parola, l'elenco dei problemi e delle soluzioni stampate dallo script
  (versione Python, ffmpeg, venv/dipendenze, token Hugging Face). Fermati e aspetta
  che l'utente risolva, a meno che non ti chieda di procedere comunque.

## Passo 2 — Esegui la trascrizione

Su Windows, senza gestire venv/dipendenze a mano (`run.bat` crea il venv della
skill e installa `requirements.txt` al primo avvio):

```bash
run.bat "<path al file audio o video>" -o output --model medium --language it
```

Oppure, con il venv della skill già attivo (`venv\Scripts\activate`):

```bash
python pipeline\main.py "<path al file audio o video>" -o output --model medium --language it
```

Se non specifichi `--model`/`--device`/`--compute-type`, la pipeline li sceglie
automaticamente in base all'hardware rilevato (`pipeline/hardware.py`: GPU/VRAM
disponibile, core CPU, RAM) e stampa la scelta fatta con la motivazione. Lascia
questi parametri vuoti a meno che l'utente non chieda esplicitamente un modello
o un device specifico.

Adatta gli altri parametri in base alla richiesta dell'utente:

| Parametro | Quando usarlo |
|---|---|
| `--model` | Solo se l'utente chiede esplicitamente una dimensione modello (`tiny/base/small/medium/large-v3`); altrimenti lascialo omesso (auto) |
| `--language` | Codice lingua (es. `it`, `en`); omettilo per auto-detect |
| `--device` | Solo se l'utente vuole forzare `cuda`/`cpu`; altrimenti lascialo omesso (auto) |
| `--min-speakers` / `--max-speakers` | Se l'utente sa quanti speaker sono presenti, aiuta la diarizzazione |
| `--denoise` | Solo se l'audio è molto rumoroso e la trascrizione risulta scarsa |
| `--hf-token` | Solo se l'utente preferisce passarlo a mano invece di impostare `HF_TOKEN` |
| `--no-cache` | Solo se l'utente vuole forzare una nuova trascrizione ignorando una cache esistente |

Se il token Hugging Face non è nell'ambiente ma l'utente te lo fornisce in chat,
passalo con `--hf-token`, non salvarlo in file di configurazione.

## Cache

I risultati di trascrizione+diarizzazione sono cachati in `.cache/` (dentro la
cartella della skill), indicizzati per contenuto audio + parametri (modello,
lingua, speaker, denoise). Se l'utente ti chiede più domande sulla stessa
registrazione (anche in sessioni diverse), non serve rilanciare la pipeline:
un secondo run sullo stesso file con gli stessi parametri userà automaticamente
la cache ed è quasi istantaneo. La cache non va né letta né modificata a mano.

## Passo 3 — Riporta il risultato

Al termine, i file generati sono in `output/<nome_file>.{txt,srt,json}`
(dentro la cartella della skill, salvo diverso `-o`).
Leggi `<nome_file>.txt` e riporta all'utente il contenuto (o un riassunto, se molto lungo),
mantenendo i tag speaker (`SPEAKER_00`, ...) e i timestamp.

## Errori durante l'esecuzione

Se `pipeline/main.py` fallisce con un errore (es. file non trovato, ffmpeg fallito,
modello di diarizzazione non accettato su Hugging Face), riporta il messaggio di
errore esatto all'utente insieme all'azione correttiva, senza tentare workaround
che bypassino la pipeline (es. non installare pacchetti alternativi, non
disattivare la diarizzazione se non richiesto).

## Struttura della skill

```
audio-transcription/
├── SKILL.md
├── check_env.py         # verifica prerequisiti, indica come risolverli
├── requirements.txt     # dipendenze Python della pipeline
├── run.bat               # crea venv, installa dipendenze, esegue la pipeline (Windows)
└── pipeline/
    ├── main.py            # entry point CLI
    ├── hardware.py          # rilevamento hardware + scelta dinamica del modello
    ├── cache.py              # cache dei risultati per file+parametri
    ├── audio_processing.py  # estrazione audio + pulizia rumore opzionale
    ├── transcription.py     # trascrizione WhisperX + diarizzazione pyannote
    └── exporters.py          # export in txt / srt / json
```
