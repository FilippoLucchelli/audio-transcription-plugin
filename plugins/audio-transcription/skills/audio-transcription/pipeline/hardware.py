"""Hardware detection and dynamic model/device selection for whisperx."""

import os

import torch


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


def recommend_settings(hardware: dict | None = None) -> dict:
    """Picks device/compute_type/model based on the available hardware.

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
    print(f"Recommended choice: model={settings['model']} device={settings['device']} "
          f"compute_type={settings['compute_type']}")
    print(f"Reason: {settings['reason']}")
