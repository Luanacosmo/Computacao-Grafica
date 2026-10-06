"""Filtros autorais: média, mediana e detector Canny."""
from __future__ import annotations
from collections import deque
import numpy as np

def _validate_kernel(size: int) -> None:
    if size < 3 or size % 2 == 0:
        raise ValueError("O tamanho da janela deve ser ímpar e >= 3.")

def mean_filter(gray: np.ndarray, size: int = 3) -> np.ndarray:
    _validate_kernel(size)
    radius = size // 2
    padded = np.pad(gray.astype(np.float32), radius, mode="edge")
    result = np.empty_like(gray, dtype=np.uint8)
    area = float(size * size)
    for y in range(gray.shape[0]):
        for x in range(gray.shape[1]):
            result[y, x] = np.clip(padded[y:y + size, x:x + size].sum() / area, 0, 255)
    return result

def median_filter(gray: np.ndarray, size: int = 3) -> np.ndarray:
    _validate_kernel(size)
    radius = size // 2
    padded = np.pad(gray, radius, mode="edge")
    result = np.empty_like(gray, dtype=np.uint8)
    for y in range(gray.shape[0]):
        for x in range(gray.shape[1]):
            result[y, x] = np.median(padded[y:y + size, x:x + size])
    return result

def _convolve(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    radius_y, radius_x = kernel.shape[0] // 2, kernel.shape[1] // 2
    padded = np.pad(image.astype(np.float32), ((radius_y, radius_y), (radius_x, radius_x)), mode="edge")
    result = np.zeros(image.shape, dtype=np.float32)
    for y in range(image.shape[0]):
        for x in range(image.shape[1]):
            result[y, x] = np.sum(padded[y:y + kernel.shape[0], x:x + kernel.shape[1]] * kernel)
    return result

def canny(gray: np.ndarray, low: int = 50, high: int = 150) -> np.ndarray:
    """Canny didático: Sobel, magnitude, supressão de não-máximos e histerese."""
    gx = _convolve(gray, np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32))
    gy = _convolve(gray, np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32))
    magnitude = np.hypot(gx, gy)
    angle = (np.rad2deg(np.arctan2(gy, gx)) + 180) % 180
    suppressed = np.zeros_like(magnitude)
    for y in range(1, gray.shape[0] - 1):
        for x in range(1, gray.shape[1] - 1):
            a = angle[y, x]
            if (0 <= a < 22.5) or (157.5 <= a < 180):
                n1, n2 = magnitude[y, x - 1], magnitude[y, x + 1]
            elif a < 67.5:
                n1, n2 = magnitude[y - 1, x + 1], magnitude[y + 1, x - 1]
            elif a < 112.5:
                n1, n2 = magnitude[y - 1, x], magnitude[y + 1, x]
            else:
                n1, n2 = magnitude[y - 1, x - 1], magnitude[y + 1, x + 1]
            if magnitude[y, x] >= n1 and magnitude[y, x] >= n2:
                suppressed[y, x] = magnitude[y, x]
    strong = suppressed >= high
    weak = (suppressed >= low) & ~strong
    result = np.zeros(gray.shape, dtype=np.uint8)
    result[strong] = 255
    queue = deque(zip(*np.nonzero(strong)))
    while queue:
        y, x = queue.popleft()
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                ny, nx = y + dy, x + dx
                if 0 <= ny < gray.shape[0] and 0 <= nx < gray.shape[1] and weak[ny, nx]:
                    weak[ny, nx] = False
                    result[ny, nx] = 255
                    queue.append((ny, nx))
    return result
