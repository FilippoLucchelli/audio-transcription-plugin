"""Cache of transcription+diarization results, to avoid re-running the
(expensive) pipeline when the same file is requested again with the same
parameters.

The cache lives in <skill_root>/.cache/ and is indexed by a hash combining
the content of the audio file actually transcribed and the parameters that
affect the result (model, language, speakers, denoise).

To keep it from growing forever, entries older than CACHE_TTL_DAYS are
dropped, and if the cache is still over MAX_CACHE_BYTES the oldest entries
(by last-modified time) are evicted until it fits. Both are configurable via
environment variables.
"""

import hashlib
import json
import os
import time
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent.parent / ".cache"

MAX_CACHE_BYTES = int(float(os.environ.get("AUDIO_TRANSCRIPTION_CACHE_MAX_MB", "2048")) * 1024 * 1024)
CACHE_TTL_SECONDS = int(float(os.environ.get("AUDIO_TRANSCRIPTION_CACHE_TTL_DAYS", "30")) * 86400)


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
    prune()


def prune() -> None:
    """Evicts expired and, if still over budget, oldest cache entries."""
    if not CACHE_DIR.exists():
        return

    now = time.time()
    entries = []
    for f in CACHE_DIR.glob("*.json"):
        try:
            stat = f.stat()
        except FileNotFoundError:
            continue
        if now - stat.st_mtime > CACHE_TTL_SECONDS:
            f.unlink(missing_ok=True)
            continue
        entries.append((stat.st_mtime, stat.st_size, f))

    total_bytes = sum(size for _, size, _ in entries)
    if total_bytes <= MAX_CACHE_BYTES:
        return

    entries.sort(key=lambda entry: entry[0])  # oldest first
    for _, size, f in entries:
        if total_bytes <= MAX_CACHE_BYTES:
            break
        f.unlink(missing_ok=True)
        total_bytes -= size
