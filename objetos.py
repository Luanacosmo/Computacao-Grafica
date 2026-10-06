"""Rotulação autoral de componentes conexos e métricas dos objetos."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
import math
import numpy as np
from morfologia import _binary

@dataclass
class Component:
    label: int
    area: int
    perimeter: int
    diameter: float
    bbox: tuple[int, int, int, int]
    centroid: tuple[float, float]

def connected_components(binary: np.ndarray, connectivity: int = 8) -> tuple[np.ndarray, list[Component]]:
    """Rotulação BFS própria; calcula área, perímetro, diâmetro e centróide."""
    src = _binary(binary)
    h, w = src.shape
    labels = np.zeros((h, w), dtype=np.int32)
    components: list[Component] = []
    neighbors = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    if connectivity == 4:
        neighbors = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    label = 0
    for y in range(h):
        for x in range(w):
            if src[y, x] == 0 or labels[y, x] != 0:
                continue
            label += 1
            q = deque([(y, x)])
            labels[y, x] = label
            pixels: list[tuple[int, int]] = []
            while q:
                cy, cx = q.popleft()
                pixels.append((cy, cx))
                for dy, dx in neighbors:
                    ny, nx = cy + dy, cx + dx
                    if 0 <= ny < h and 0 <= nx < w and src[ny, nx] and labels[ny, nx] == 0:
                        labels[ny, nx] = label
                        q.append((ny, nx))
            area = len(pixels)
            ys = [p[0] for p in pixels]; xs = [p[1] for p in pixels]
            pixel_set = set(pixels)
            perimeter = sum(any((y0 + dy, x0 + dx) not in pixel_set for dy, dx in [(-1, 0), (1, 0), (0, -1), (0, 1)]) for y0, x0 in pixels)
            # Diâmetro exato para componentes pequenos; aproximação pelo diâmetro da caixa para grandes.
            if area <= 2500:
                diameter = max((math.hypot(y1 - y2, x1 - x2) for y1, x1 in pixels for y2, x2 in pixels), default=0.0)
            else:
                diameter = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
            components.append(Component(label, area, perimeter, diameter,
                                        (min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1),
                                        (float(sum(xs) / area), float(sum(ys) / area))))
    return labels, components
