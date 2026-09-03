"""Cache of transcription+diarization results, to avoid re-running the
(expensive) pipeline when the same file is requested again with the same
parameters.

The cache lives in <skill_root>/.cache/ and is indexed by a hash combining
the content of the audio file actually transcribed and the parameters that
affect the result (model, language, speakers, denoise).
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
    """Computes the cache key from the audio content + pipeline parameters."""
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
