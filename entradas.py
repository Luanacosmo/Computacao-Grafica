"""Aquisição: carregamento de imagem e abertura de câmera/vídeo."""
from __future__ import annotations
from pathlib import Path
from typing import Union
import cv2
import numpy as np


def load_image(path: Union[str, Path]) -> np.ndarray:
    image = cv2.imread(str(path))
    if image is None:
        raise FileNotFoundError(f"Não foi possível abrir a imagem: {path}")
    return image


def open_video(source: Union[str, int] = 0) -> cv2.VideoCapture:
    source_value = int(source) if isinstance(source, str) and source.strip().isdigit() else source
    capture = cv2.VideoCapture(source_value)
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Não foi possível abrir a fonte de vídeo: {source}")
    return capture
