"""Cache dei risultati di trascrizione+diarizzazione, per evitare di rilanciare
la pipeline (costosa) quando lo stesso file viene richiesto di nuovo con gli
stessi parametri.

La cache vive in <skill_root>/.cache/ ed è indicizzata su un hash che combina
il contenuto del file audio effettivamente trascritto e i parametri che
influenzano il risultato (modello, lingua, speaker, denoise).
"""

import hashlib
import json
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"


def _hash_file(path: str, chunk_size: int = 1 << 20) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_key(audio_path: str, **params) -> str:
    """Calcola la chiave di cache da contenuto audio + parametri della pipeline."""
    file_hash = _hash_file(audio_path)
    params_str = json.dumps(params, sort_keys=True)
    return hashlib.sha256(f"{file_hash}:{params_str}".encode("utf-8")).hexdigest()


def load(key: str) -> dict | None:
    cache_file = CACHE_DIR / f"{key}.json"
    if not cache_file.exists():
        return None
    return json.loads(cache_file.read_text(encoding="utf-8"))


def save(key: str, result: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{key}.json"
    cache_file.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
