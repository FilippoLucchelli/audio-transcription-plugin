"""Rilevamento hardware e scelta dinamica di modello/device per whisperx."""

import os

import torch


def detect_hardware() -> dict:
    """Rileva CUDA/VRAM, numero di core CPU e RAM disponibili sulla macchina corrente."""
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


def recommend_settings(hardware: dict | None = None) -> dict:
    """Sceglie device/compute_type/model in base all'hardware disponibile.

    Ritorna anche 'reason', una spiegazione leggibile della scelta (per il log/utente).
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
        reason = f"GPU CUDA rilevata con ~{vram:.1f} GB VRAM"
    else:
        device = "cpu"
        compute_type = "int8"
        cpu_count = hw["cpu_count"]
        ram = hw["ram_gb"]
        if ram is None:
            model = "small"
            reason = f"Nessuna GPU CUDA; {cpu_count} core CPU (RAM non rilevabile, uso stima prudente)"
        elif cpu_count >= 8 and ram >= 16:
            model = "medium"
            reason = f"Nessuna GPU CUDA; {cpu_count} core CPU e ~{ram:.1f} GB RAM"
        elif cpu_count >= 4 and ram >= 8:
            model = "small"
            reason = f"Nessuna GPU CUDA; {cpu_count} core CPU e ~{ram:.1f} GB RAM"
        else:
            model = "base"
            reason = f"Nessuna GPU CUDA; {cpu_count} core CPU e ~{ram:.1f} GB RAM (risorse limitate)"

    return {
        "device": device,
        "compute_type": compute_type,
        "model": model,
        "reason": reason,
        "hardware": hw,
    }


if __name__ == "__main__":
    settings = recommend_settings()
    print(f"Hardware: {settings['hardware']}")
    print(f"Scelta consigliata: model={settings['model']} device={settings['device']} "
          f"compute_type={settings['compute_type']}")
    print(f"Motivo: {settings['reason']}")
