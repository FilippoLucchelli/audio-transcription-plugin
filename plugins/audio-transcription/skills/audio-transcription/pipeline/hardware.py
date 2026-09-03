"""Hardware detection and dynamic model/device selection for whisperx."""

import os

import torch

MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

# Minimum model size for non-English languages: the smallest models (tiny/base)
# are trained mostly on English and degrade a lot on other languages, so bump
# up to at least "small" whenever a non-English language is requested.
MIN_MODEL_NON_ENGLISH = "small"

# Rough real-time factor (seconds of compute per second of audio) per
# (device, model). These are illustrative ballpark figures, not measured on
# this machine: actual speed varies with CPU/GPU generation, audio content,
# etc. Used only to give the user a rough time estimate before running.
RTF_ESTIMATES = {
    ("cpu", "tiny"): 0.3,
    ("cpu", "base"): 0.5,
    ("cpu", "small"): 1.0,
    ("cpu", "medium"): 2.5,
    ("cpu", "large-v3"): 5.0,
    ("cuda", "tiny"): 0.05,
    ("cuda", "base"): 0.08,
    ("cuda", "small"): 0.15,
    ("cuda", "medium"): 0.3,
    ("cuda", "large-v3"): 0.5,
}
# Extra overhead for alignment + diarization on top of the raw transcription
# time, expressed as a fraction of the transcription time.
DIARIZATION_OVERHEAD_FACTOR = 0.4


def detect_hardware() -> dict:
    """Detects CUDA/VRAM, CPU core count, and RAM available on the current machine."""
    cuda_available = torch.cuda.is_available()
    vram_gb = None
    if cuda_available:
        vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)

    cpu_count = os.cpu_count() or 1

    ram_gb = None
    try:
        import psutil

        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        pass

    return {
        "cuda": cuda_available,
        "vram_gb": vram_gb,
        "cpu_count": cpu_count,
        "ram_gb": ram_gb,
    }


def recommend_settings(hardware: dict | None = None, language: str | None = None) -> dict:
    """Picks device/compute_type/model based on the available hardware and,
    optionally, the target language.

    Also returns 'reason', a human-readable explanation of the choice (for
    logging/reporting to the user).
    """
    hw = hardware or detect_hardware()

    if hw["cuda"]:
        device = "cuda"
        compute_type = "float16"
        vram = hw["vram_gb"] or 0
        if vram >= 10:
            model = "large-v3"
        elif vram >= 5:
            model = "medium"
        else:
            model = "small"
        reason = f"CUDA GPU detected with ~{vram:.1f} GB VRAM"
    else:
        device = "cpu"
        compute_type = "int8"
        cpu_count = hw["cpu_count"]
        ram = hw["ram_gb"]
        if ram is None:
            model = "small"
            reason = f"No CUDA GPU; {cpu_count} CPU cores (RAM not detectable, using a conservative estimate)"
        elif cpu_count >= 8 and ram >= 16:
            model = "medium"
            reason = f"No CUDA GPU; {cpu_count} CPU cores and ~{ram:.1f} GB RAM"
        elif cpu_count >= 4 and ram >= 8:
            model = "small"
            reason = f"No CUDA GPU; {cpu_count} CPU cores and ~{ram:.1f} GB RAM"
        else:
            model = "base"
            reason = f"No CUDA GPU; {cpu_count} CPU cores and ~{ram:.1f} GB RAM (limited resources)"

    if language and language.lower() not in ("en", "english"):
        if MODEL_SIZES.index(model) < MODEL_SIZES.index(MIN_MODEL_NON_ENGLISH):
            model = MIN_MODEL_NON_ENGLISH
            reason += f"; bumped to '{model}' for non-English language '{language}' (small models are unreliable outside English)"

    return {
        "device": device,
        "compute_type": compute_type,
        "model": model,
        "reason": reason,
        "hardware": hw,
    }


def estimate_processing_seconds(audio_seconds: float, device: str, model: str) -> float:
    """Very rough estimate of wall-clock processing time, for reporting to the
    user before running the (potentially long) pipeline. Not a guarantee."""
    rtf = RTF_ESTIMATES.get((device, model))
    if rtf is None:
        rtf = RTF_ESTIMATES.get(("cpu", "medium"))
    return audio_seconds * rtf * (1 + DIARIZATION_OVERHEAD_FACTOR)


if __name__ == "__main__":
    settings = recommend_settings()
    print(f"Hardware: {settings['hardware']}")
    print(f"Recommended choice: model={settings['model']} device={settings['device']} "
          f"compute_type={settings['compute_type']}")
    print(f"Reason: {settings['reason']}")
