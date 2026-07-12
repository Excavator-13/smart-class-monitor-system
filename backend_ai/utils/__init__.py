"""Utility helpers for the AI service."""


def resolve_device(device: str | None = None) -> str:
    if device not in (None, "auto"):
        return device
    try:
        import torch
    except ImportError:
        return "cpu"
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"