"""Operações morfológicas autorais sobre imagens binárias."""
from __future__ import annotations
import numpy as np

def _validate_kernel(size: int) -> None:
    if size < 3 or size % 2 == 0:
        raise ValueError("O tamanho da janela deve ser ímpar e >= 3.")

def _binary(image: np.ndarray) -> np.ndarray:
    return np.where(image > 0, 255, 0).astype(np.uint8)

def erode(binary: np.ndarray, size: int = 3) -> np.ndarray:
    _validate_kernel(size)
    r = size // 2
    src = _binary(binary)
    padded = np.pad(src, r, mode="constant", constant_values=0)
    out = np.zeros_like(src)
    for y in range(src.shape[0]):
        for x in range(src.shape[1]):
            out[y, x] = 255 if np.all(padded[y:y + size, x:x + size] == 255) else 0
    return out

def dilate(binary: np.ndarray, size: int = 3) -> np.ndarray:
    _validate_kernel(size)
    r = size // 2
    src = _binary(binary)
    padded = np.pad(src, r, mode="constant", constant_values=0)
    out = np.zeros_like(src)
    for y in range(src.shape[0]):
        for x in range(src.shape[1]):
            out[y, x] = 255 if np.any(padded[y:y + size, x:x + size] == 255) else 0
    return out

def opening(binary: np.ndarray, size: int = 3) -> np.ndarray:
    return dilate(erode(binary, size), size)

def closing(binary: np.ndarray, size: int = 3) -> np.ndarray:
    return erode(dilate(binary, size), size)
