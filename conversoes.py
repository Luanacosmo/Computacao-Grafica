"""Conversões de imagens e vídeos: cinza, negativo e Otsu."""
from __future__ import annotations
import numpy as np
from histograma import histogram

def to_gray(image: np.ndarray) -> np.ndarray:
    """Converte BGR para cinza pela média dos três canais (Lista 1)."""
    if image.ndim == 2:
        return image.copy()
    return ((image[:, :, 0].astype(np.uint16) // 3) +
            (image[:, :, 1].astype(np.uint16) // 3) +
            (image[:, :, 2].astype(np.uint16) // 3)).astype(np.uint8)

def negative(image: np.ndarray) -> np.ndarray:
    return (255 - image).astype(np.uint8)

def otsu(gray: np.ndarray) -> tuple[int, np.ndarray]:
    hist = histogram(gray)
    total = gray.size
    total_sum = sum(i * int(hist[i]) for i in range(256))
    background_weight = 0
    background_sum = 0
    best_variance = -1.0
    threshold = 0
    for t in range(256):
        background_weight += int(hist[t])
        if background_weight == 0:
            continue
        foreground_weight = total - background_weight
        if foreground_weight == 0:
            break
        background_sum += t * int(hist[t])
        mean_b = background_sum / background_weight
        mean_f = (total_sum - background_sum) / foreground_weight
        variance = background_weight * foreground_weight * (mean_b - mean_f) ** 2
        if variance > best_variance:
            best_variance, threshold = variance, t
    # Usar > evita que, quando o melhor limiar é 0, o fundo de intensidade 0
    # seja classificado como primeiro plano (caso comum em imagens binárias).
    return threshold, np.where(gray > threshold, 255, 0).astype(np.uint8)
