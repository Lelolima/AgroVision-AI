"""
Detector de Animais - YOLOv5/Ultralytics
Detecção de gado e outros animais em imagens e vídeos
"""

import torch
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass

from agrovision.utils.logger import setup_logger
from agrovision.config.settings import settings

logger = setup_logger(__name__)


@dataclass
class Detection:
    """Classe para representar uma detecção"""
    bbox: List[int]  # [x1, y1, x2, y2]
    confidence: float
    class_id: int
    class_name: str
    track_id: Optional[int] = None
    weight_est: Optional[float] = None
    behavior: Optional[str] = None


class AnimalDetector:
    """
    Detector de animais usando YOLOv5

    Suporta:
    - Modelos Ultralytics YOLOv5/v8
    - Torch hub models
    - Modelos ONNX para edge
    - Modo simulação quando modelos não estão disponíveis
    """

    # Classes de animais suportadas
    ANIMAL_CLASSES = {
        0: "vaca",
        1: "bezerro",
        2: "touro",
        3: "cavalo",
        4: "porco",
        5: "ovelha",
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        confidence_threshold: float = None,
        device: Optional[str] = None,
        simulate: bool = False
    ):
        """
        Inicializa o detector.

        Args:
            model_path: Caminho para o modelo pré-treinado
            confidence_threshold: Threshold de confiança para detecções
            device: Dispositivo ('cuda', 'cpu', ou None para auto)
            simulate: Se True, usa modo simulação
        """
        self.model_path = model_path or settings.YOLO_MODEL
        self.confidence_threshold = confidence_threshold or settings.CONFIDENCE_THRESHOLD

        # Selecionar dispositivo
        if device:
            self.device = torch.device(device)
        else:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        logger.info(f"Usando dispositivo: {self.device}")

        self.model = None
        self.simulate = simulate

        # Carregar modelo
        if not simulate:
            self._load_model()
        else:
            logger.warning("Detector em modo simulação")

    def _load_model(self):
        """Carrega o modelo YOLO"""
        try:
            from ultralytics import YOLO

            model_path = Path(self.model_path)

            # Verificar se o modelo existe
            if not model_path.exists():
                logger.warning(
                    f"Modelo não encontrado: {model_path}. "
                    "Execute: python scripts/download_models.py"
                )
                logger.info("Alternando para modo simulação")
                self.simulate = True
                return

            # Carregar modelo
            self.model = YOLO(str(model_path))
            self.model.to(self.device)

            logger.info(f"Modelo carregado: {model_path}")

        except ImportError:
            logger.error("Ultralytics não instalado. Execute: pip install ultralytics")
            self.simulate = True
        except Exception as e:
            logger.error(f"Erro ao carregar modelo: {e}")
            self.simulate = True

    def detect(
        self,
        image: Union[np.ndarray, str, Path]
    ) -> List[Detection]:
        """
        Detecta animais em uma imagem.

        Args:
            image: Imagem (numpy array) ou caminho da imagem

        Returns:
            Lista de detecções
        """
        if self.simulate:
            return self._simulate_detection(image)

        try:
            # Executar inferência
            results = self.model(image, conf=self.confidence_threshold, verbose=False)

            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue

                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    conf = float(box.conf[0])
                    cls_id = int(box.cls[0])

                    detections.append(Detection(
                        bbox=[int(x1), int(y1), int(x2), int(y2)],
                        confidence=conf,
                        class_id=cls_id,
                        class_name=self.ANIMAL_CLASSES.get(cls_id, "animal")
                    ))

            logger.debug(f"Detectados {len(detections)} animais")
            return detections

        except Exception as e:
            logger.error(f"Erro na detecção: {e}")
            return []

    def _simulate_detection(self, image) -> List[Detection]:
        """Gera detecções simuladas para testes/demonstração"""
        import random

        # Simular 1-5 animais
        num_animals = random.randint(1, 5)
        detections = []

        for i in range(num_animals):
            detections.append(Detection(
                bbox=[
                    random.randint(50, 500),
                    random.randint(50, 300),
                    random.randint(80, 150),
                    random.randint(60, 120)
                ],
                confidence=random.uniform(0.85, 0.99),
                class_id=random.randint(0, 2),
                class_name=random.choice(["vaca", "bezerro", "touro"])
            ))

        return detections

    def detect_batch(
        self,
        images: List[Union[np.ndarray, str]]
    ) -> List[List[Detection]]:
        """
        Detecta animais em múltiplas imagens.

        Args:
            images: Lista de imagens

        Returns:
            Lista de listas de detecções
        """
        return [self.detect(img) for img in images]

    def get_model_info(self) -> Dict:
        """Retorna informações do modelo"""
        return {
            "model_path": str(self.model_path),
            "device": str(self.device),
            "confidence_threshold": self.confidence_threshold,
            "simulate_mode": self.simulate,
            "classes": list(self.ANIMAL_CLASSES.values())
        }