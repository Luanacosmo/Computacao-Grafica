"""Histograma calculado manualmente e sua visualização."""
from __future__ import annotations
import cv2
import numpy as np

def histogram(gray: np.ndarray) -> np.ndarray:
    hist = np.zeros(256, dtype=np.int64)
    for value in gray.ravel():
        hist[int(value)] += 1
    return hist

def draw_histogram(gray: np.ndarray, title: str = "Histograma") -> np.ndarray:
    hist = histogram(gray).astype(np.float64)
    canvas = np.full((420, 700, 3), 255, dtype=np.uint8)
    max_value = max(float(hist.max()), 1.0)
    for i in range(256):
        x = int(i * 699 / 255)
        height = int(hist[i] / max_value * 360)
        cv2.line(canvas, (x, 390), (x, 390 - height), (40, 40, 40), 1)
    cv2.putText(canvas, title, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, .8, (0, 0, 0), 2)
    cv2.putText(canvas, "0", (5, 410), cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 0, 0), 1)
    cv2.putText(canvas, "255", (660, 410), cv2.FONT_HERSHEY_SIMPLEX, .45, (0, 0, 0), 1)
    return canvas
