"""Processamento de vídeo, detecção automática de caneta e áudio."""
from __future__ import annotations
from typing import Optional
import cv2
import numpy as np
from audios import play_music
from caneta import PenDetector
from conversoes import to_gray, negative, otsu
from entradas import open_video
from filtros import canny, mean_filter, median_filter
from morfologia import closing, dilate, erode, opening


def choose_tracker():
    """Retorna o primeiro rastreador disponível nesta instalação do OpenCV."""
    for name in ("TrackerCSRT_create", "TrackerKCF_create", "TrackerMIL_create"):
        factory = getattr(cv2, name, None)
        if factory is None and hasattr(cv2, "legacy"):
            factory = getattr(cv2.legacy, name, None)
        if factory is not None:
            return factory, name.replace("Tracker", "").replace("_create", "")
    return None, "indisponível"


def show(name: str, image: np.ndarray) -> None:
    try:
        cv2.imshow(name, image)
        cv2.waitKey(1)
    except cv2.error:
        print(f"[visualização indisponível] {name}: {image.shape}")


def process_video(source: str = "0", music: Optional[str] = None) -> None:
    capture = open_video(source)
    detector = PenDetector()
    played = False
    operation = None
    print("Vídeo: YOLO detecta canetas automaticamente; q encerra; g cinza; n negativo; o Otsu; a média; d mediana; c Canny; e erosão; l dilatação; b abertura; f fechamento.")
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        try:
            display, detections = detector.annotate(frame)
        except Exception as exc:
            capture.release(); cv2.destroyAllWindows()
            raise RuntimeError(f"Falha na detecção YOLO: {exc}") from exc
        if detections and music and not played:
            played = play_music(music)
            if played:
                print("Caneta reconhecida: música acionada.")
        if operation is not None:
            result = operation(frame)
            show("Resultado", result)
        show("Vídeo", display)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord("g"): operation = lambda f: to_gray(f)
        elif key == ord("n"): operation = lambda f: negative(f)
        elif key == ord("o"): operation = lambda f: otsu(to_gray(f))[1]
        elif key == ord("a"): operation = lambda f: mean_filter(to_gray(f), 3)
        elif key == ord("d"): operation = lambda f: median_filter(to_gray(f), 3)
        elif key == ord("c"): operation = lambda f: canny(to_gray(f))
        elif key in (ord("e"), ord("l"), ord("b"), ord("f")):
            _, binary = otsu(to_gray(frame))
            operation = {ord("e"): erode, ord("l"): dilate, ord("b"): opening, ord("f"): closing}[key]
            operation = lambda f, fn=operation: fn(otsu(to_gray(f))[1], 3)
    capture.release(); cv2.destroyAllWindows()
