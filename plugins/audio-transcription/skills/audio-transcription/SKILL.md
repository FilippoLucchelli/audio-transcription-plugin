---
name: audio-transcription
description: Trascrive e diarizza (identifica gli speaker) l'audio di un file audio o video usando la pipeline locale bundled in questa skill (WhisperX + pyannote). Usa questa skill ogni volta che l'utente ha un file audio/video (registrazione, chiamata, meeting, podcast — es. Teams) e vuole sapere cosa contiene o cosa è stato detto, anche se non usa parole come "trascrivi": rientrano anche richieste come "ascolta questo video", "di cosa parla", "riassumi l'audio/la call", "cosa si dice in questo file", "chi ha parlato di più/quanto", "sottotitola", "estrai il testo". In tutti questi casi la skill genera prima la trascrizione con gli speaker, poi risponde alla domanda specifica.
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

Senza gestire venv/dipendenze a mano (`run.bat`/`run.sh` creano il venv della
skill e installano `requirements.txt` al primo avvio):

```bash
run.bat "<path al file audio o video>" -o output --model medium --language it   # Windows
./run.sh "<path al file audio o video>" -o output --model medium --language it  # Linux/macOS
```

Oppure, con il venv della skill già attivo (`venv\Scripts\activate` su Windows,
`source venv/bin/activate` su Linux/macOS):

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

### Token Hugging Face

Se `check_env.py` segnala che `HF_TOKEN` non è impostato, l'utente ha tre modi
per fornirlo (in ordine di comodità):

1. **Variabile d'ambiente permanente** — impostata una volta a livello di sistema,
   disponibile sempre: `setx HF_TOKEN "hf_xxx"` su Windows (riavvia il terminale
   dopo), oppure aggiungerla a `~/.bashrc`/`~/.zshrc` su Linux/macOS.
2. **Variabile d'ambiente solo per la sessione corrente** — impostata nel terminale
   prima di lanciare Claude Code (`$env:HF_TOKEN=...` su PowerShell, `export
   HF_TOKEN=...` su Linux/macOS); vale solo per quella sessione.
3. **Fornito direttamente in chat** — l'utente te lo scrive in un messaggio; in
   questo caso passalo con `--hf-token` alla singola esecuzione, **non salvarlo**
   in nessun file di configurazione né in cache.

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
├── run.sh                # equivalente di run.bat per Linux/macOS
└── pipeline/
    ├── main.py            # entry point CLI
    ├── hardware.py          # rilevamento hardware + scelta dinamica del modello
    ├── cache.py              # cache dei risultati per file+parametri
    ├── audio_processing.py  # estrazione audio + pulizia rumore opzionale
    ├── transcription.py     # trascrizione WhisperX + diarizzazione pyannote
    └── exporters.py          # export in txt / srt / json
```
