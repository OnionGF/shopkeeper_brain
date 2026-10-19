"""设备选择：优先 CUDA，其次 Apple MPS，否则 CPU。"""
from __future__ import annotations

import torch


def get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")
