"""Detecção de caneta em vídeo usando YOLO-World e classes textuais."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import cv2
import numpy as np


@dataclass
class PenDetection:
    box: tuple[int, int, int, int]
    confidence: float
    label: str


class PenDetector:
    """Detector de canetas; carrega o modelo sob demanda para não atrasar a GUI."""

    def __init__(self, model_name: str = "yolov8s-world.pt", confidence: float = 0.25) -> None:
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError(
                "YOLO não está instalado. YOLOv8 é o modelo, não o nome do pacote. "
                "Execute: python -m pip install -r requirements.txt"
            ) from exc
        self.confidence = confidence
        try:
            self.model = YOLO(model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Não foi possível baixar/carregar {model_name}. "
                "Verifique a internet e execute novamente o botão Detectar caneta."
            ) from exc
        # YOLO-World permite procurar objetos descritos por texto, inclusive caneta.
        try:
            self.model.set_classes(["pen", "ballpoint pen", "marker pen", "pencil"])
        except Exception as exc:
            raise RuntimeError(
                "O YOLO-World foi carregado, mas falta a dependência CLIP. "
                "Execute: python -m pip install -r requirements.txt"
            ) from exc
        self.labels = ["caneta", "caneta esferográfica", "canetão", "lápis"]

    def detect(self, frame: np.ndarray) -> list[PenDetection]:
        results = self.model.predict(frame, conf=self.confidence, verbose=False)
        detections: list[PenDetection] = []
        for result in results:
            if result.boxes is None:
                continue
            for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
                x1, y1, x2, y2 = map(int, box.tolist())
                index = int(cls.item())
                label = self.labels[index] if index < len(self.labels) else "caneta"
                detections.append(PenDetection((x1, y1, x2 - x1, y2 - y1), float(conf.item()), label))
        return detections

    def annotate(self, frame: np.ndarray) -> tuple[np.ndarray, list[PenDetection]]:
        detections = self.detect(frame)
        output = frame.copy()
        for detection in detections:
            x, y, w, h = detection.box
            cv2.rectangle(output, (x, y), (x + w, y + h), (0, 220, 0), 2)
            cv2.putText(
                output,
                f"{detection.label} {detection.confidence:.0%}",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 220, 0),
                2,
            )
        cv2.putText(output, f"Canetas: {len(detections)}", (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 220, 0), 2)
        return output, detections
