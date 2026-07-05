"""
Estimativa de Peso - LightGBM
Estima peso de animais baseado em dimensões corporais
"""

import numpy as np
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass

from agrovision.utils.logger import setup_logger
from agrovision.config.settings import settings

logger = setup_logger(__name__)


@dataclass
class WeightEstimate:
    """Resultado da estimativa de peso"""
    weight_kg: float
    confidence: float
    method: str
    body_dimensions: Dict[str, float]


class WeightEstimator:
    """
    Estimativa de peso baseada em dimensões corporais extraídas das imagens.

    Usa LightGBM treinado com dados de:
    - Altura do dorso
    - Comprimento corporal
    - Largura do torso
    - Profundidade do peito

    Retorna estimativa em kg com intervalo de confiança.
    """

    # Coeficientes base para fórmula simplificada (quando modelo não disponível)
    # Baseado em: Weight = a * (height^2) * length + b
    BREED_COEFFICIENTS = {
        "nelore": {"a": 0.00015, "b": 50},
        "angu s": {"a": 0.00018, "b": 60},
        "holandes": {"a": 0.00020, "b": 80},
        "default": {"a": 0.00017, "b": 55},
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        breed: str = "default"
    ):
        """
        Inicializa o estimador.

        Args:
            model_path: Caminho para o modelo LightGBM treinado
            breed: Raça do animal (afeta coeficientes)
        """
        self.model_path = model_path or str(settings.MODEL_DIR / "weight_model.pkl")
        self.breed = breed.lower()
        self.model = None
        self.loaded = False

        self._load_model()

    def _load_model(self):
        """Carrega modelo LightGBM"""
        try:
            import lightgbm as lgb

            model_file = Path(self.model_path)
            if model_file.exists():
                self.model = lgb.Booster(model_file=str(model_file))
                self.loaded = True
                logger.info(f"Modelo de peso carregado: {model_file}")
            else:
                logger.warning(
                    f"Modelo de peso não encontrado: {model_file}. "
                    "Usando fórmula simplificada."
                )
        except ImportError:
            logger.warning("LightGBM não instalado. Usando fórmula simplificada.")
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo de peso: {e}")

    def estimate(
        self,
        bbox: List[int],
        image_height: int,
        image_width: int,
        confidence: float = 0.9
    ) -> WeightEstimate:
        """
        Estima peso baseado no bounding box.

        Args:
            bbox: [x1, y1, x2, y2] do animal
            image_height: Altura da imagem em pixels
            image_width: Largura da imagem em pixels
            confidence: Confiança da detecção

        Returns:
            WeightEstimate com peso estimado em kg
        """
        # Extrair dimensões do bbox
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        aspect_ratio = width / max(height, 1)

        # Normalizar dimensões (aproximação da distância da câmera)
        norm_height = height / image_height
        norm_width = width / image_width

        # Calcular dimensões corporais aproximadas
        body_dimensions = {
            "height": norm_height,
            "length": norm_width,
            "aspect_ratio": aspect_ratio,
            "area": norm_height * norm_width
        }

        # Estimar peso
        if self.loaded and self.model is not None:
            # Usar modelo ML
            weight = self._predict_ml(body_dimensions)
            method = "lightgbm"
        else:
            # Usar fórmula simplificada
            weight = self._predict_simple(body_dimensions)
            method = "formula"

        # Ajustar confiança
        adjusted_confidence = confidence * 0.8  # Reduzir confiança base

        return WeightEstimate(
            weight_kg=max(50, min(800, weight)),  # Bounds realistas
            confidence=adjusted_confidence,
            method=method,
            body_dimensions=body_dimensions
        )

    def _predict_ml(self, dims: Dict[str, float]) -> float:
        """Predição usando modelo ML"""
        try:
            import lightgbm as lgb

            features = np.array([[
                dims["height"],
                dims["length"],
                dims["aspect_ratio"],
                dims["area"]
            ]], dtype=np.float32)

            pred = self.model.predict(features)[0]
            return float(pred)
        except Exception as e:
            logger.error(f"Erro na predição ML: {e}")
            return self._predict_simple(dims)

    def _predict_simple(self, dims: Dict[str, float]) -> float:
        """Predição usando fórmula simplificada"""
        coeffs = self.BREED_COEFFICIENTS.get(self.breed, self.BREED_COEFFICIENTS["default"])

        # Weight = a * (height^2) * length * scale + b
        # Scale factors para converter pixels normalizados para metros aproximados
        scale = 2.5  # Fator de escala empírico

        height_m = dims["height"] * scale
        length_m = dims["length"] * scale

        weight = (
            coeffs["a"] * (height_m ** 2) * length_m * 1000 +
            coeffs["b"]
        )

        return weight

    def estimate_batch(
        self,
        detections: List,
        image_height: int,
        image_width: int
    ) -> List[WeightEstimate]:
        """
        Estima peso para múltiplas detecções.

        Args:
            detections: Lista de detecções ou tracked animals
            image_height: Altura da imagem
            image_width: Largura da imagem

        Returns:
            Lista de WeightEstimate
        """
        estimates = []

        for det in detections:
            if hasattr(det, 'bbox'):
                bbox = det.bbox
                confidence = getattr(det, 'confidence', 0.9)
            else:
                bbox = det.get('bbox', [0, 0, 100, 100])
                confidence = det.get('confidence', 0.9)

            estimate = self.estimate(bbox, image_height, image_width, confidence)
            estimates.append(estimate)

        return estimates

    def get_breed_info(self) -> Dict:
        """Retorna informações sobre raças suportadas"""
        return {
            "current_breed": self.breed,
            "supported_breeds": list(self.BREED_COEFFICIENTS.keys()),
            "coefficients": self.BREED_COEFFICIENTS.get(
                self.breed, self.BREED_COEFFICIENTS["default"]
            )
        }