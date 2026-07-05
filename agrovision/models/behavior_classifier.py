"""
Classificador de Comportamento - CNN 3D
Classifica padrões de comportamento animal: calmo, agitado, alimentando, etc.
"""

import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from enum import Enum
from collections import Counter

from agrovision.utils.logger import setup_logger

logger = setup_logger(__name__)


class Behavior(str, Enum):
    """Comportamentos suportados"""
    CALMO = "calmo"
    AGITADO = "agitado"
    ALIMENTANDO = "alimentando"
    CAMINHANDO = "caminhando"
    DEITADO = "deitado"
    INTERAGINDO = "interagindo"


class BehaviorClassifier:
    """
    Classificador de comportamento usando CNN 3D ou heurísticas.

    Analisa sequência de frames para identificar padrões:
    - Calmo: Pouco movimento, posição consistente
    - Agitado: Movimento rápido e errático
    - Alimentando: Cabeça baixa, movimento consistente
    - Caminhando: Direção consistente
    - Deitado: Altura reduzida, pouco movimento
    - Interagindo: Proximidade com outros animais
    """

    # Thresholds para classificação heurística
    MOVEMENT_THRESHOLDS = {
        "calmo": {"max_motion": 0.1, "min_consistency": 0.8},
        "agitado": {"min_motion": 0.5, "max_consistency": 0.3},
        "alimentando": {"head_down_ratio": 0.6, "motion_range": 0.2},
        "caminhando": {"direction_consistency": 0.7, "min_motion": 0.15},
        "deitado": {"height_ratio": 0.5, "max_motion": 0.15},
        "interagindo": {"proximity_threshold": 50, "motion_correlation": 0.6},
    }

    def __init__(
        self,
        model_path: Optional[str] = None,
        sequence_length: int = 16,
        use_heuristics: bool = True
    ):
        """
        Inicializa o classificador.

        Args:
            model_path: Caminho para o modelo CNN 3D
            sequence_length: Número de frames na sequência
            use_heuristics: Usar classificação heurística se modelo indisponível
        """
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.use_heuristics = use_heuristics

        self.model = None
        self.loaded = False

        # Buffer de sequências por animal
        self.sequence_buffers: Dict[int, List] = {}

        self._load_model()

    def _load_model(self):
        """Carrega modelo CNN 3D"""
        try:
            import torch
            import torch.nn as nn

            model_file = Path(self.model_path) if self.model_path else None

            if model_file and model_file.exists():
                # Carregar modelo
                self.model = self._build_cnn3d()
                checkpoint = torch.load(model_file, map_location='cpu')
                self.model.load_state_dict(checkpoint['state_dict'])
                self.model.eval()
                self.loaded = True
                logger.info(f"Modelo de comportamento carregado: {model_file}")
            else:
                logger.info("Usando classificação heurística (modelo não encontrado)")
        except ImportError:
            logger.info("PyTorch não disponível para CNN. Usando heurísticas.")
        except Exception as e:
            logger.warning(f"Erro ao carregar modelo: {e}. Usando heurísticas.")

    def _build_cnn3d(self):
        """Constroi arquitetura CNN 3D simples"""
        import torch.nn as nn

        class SimpleCNN3D(nn.Module):
            def __init__(self, num_classes=6):
                super().__init__()
                self.features = nn.Sequential(
                    nn.Conv3d(3, 16, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool3d(2),
                    nn.Conv3d(16, 32, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.MaxPool3d(2),
                    nn.Conv3d(32, 64, kernel_size=3, padding=1),
                    nn.ReLU(),
                    nn.AdaptiveAvgPool3d(1),
                )
                self.classifier = nn.Sequential(
                    nn.Flatten(),
                    nn.Linear(64, 32),
                    nn.ReLU(),
                    nn.Dropout(0.5),
                    nn.Linear(32, num_classes),
                )

            def forward(self, x):
                x = self.features(x)
                x = self.classifier(x)
                return x

        return SimpleCNN3D()

    def classify(
        self,
        track_id: int,
        frames: List[np.ndarray],
        bboxes: List[List[int]],
        other_tracks: Optional[List[int]] = None
    ) -> Tuple[Behavior, float]:
        """
        Classifica comportamento de um animal.

        Args:
            track_id: ID do track do animal
            frames: Lista de frames da sequência
            bboxes: Lista de bboxes correspondentes
            other_tracks: IDs de outros animais próximos (para interação)

        Returns:
            Tupla (Behavior, confiança)
        """
        # Atualizar buffer de sequência
        if track_id not in self.sequence_buffers:
            self.sequence_buffers[track_id] = []

        self.sequence_buffers[track_id].extend(list(zip(frames, bboxes)))

        # Manter apenas sequência recente
        max_buffer = self.sequence_length * 2
        if len(self.sequence_buffers[track_id]) > max_buffer:
            self.sequence_buffers[track_id] = \
                self.sequence_buffers[track_id][-max_buffer:]

        # Extrair features
        features = self._extract_features(
            self.sequence_buffers[track_id],
            other_tracks
        )

        # Classificar
        if self.loaded and len(frames) >= self.sequence_length:
            behavior, confidence = self._classify_ml(features)
        else:
            behavior, confidence = self._classify_heuristic(features)

        return behavior, confidence

    def _extract_features(
        self,
        sequence: List[Tuple],
        other_tracks: Optional[List[int]] = None
    ) -> Dict:
        """Extrai features da sequência para classificação"""
        if not sequence:
            return self._empty_features()

        bboxes = [s[1] for s in sequence]

        # Features de movimento
        positions = [(b[0] + b[2]) / 2 for b in bboxes]  # Centro X
        velocities = np.diff(positions)

        # Features de forma
        heights = [b[3] - b[1] for b in bboxes]
        widths = [b[2] - b[0] for b in bboxes]
        aspect_ratios = [w / max(h, 1) for w, h in zip(widths, heights)]

        # Features estatísticas
        motion_energy = np.sum(np.abs(velocities))
        motion_variance = np.var(velocities)
        direction_consistency = np.mean(np.sign(velocities)) ** 2
        height_consistency = np.std(heights) / max(np.mean(heights), 1)
        avg_aspect_ratio = np.mean(aspect_ratios)

        return {
            "motion_energy": motion_energy,
            "motion_variance": motion_variance,
            "direction_consistency": direction_consistency,
            "height_consistency": height_consistency,
            "avg_aspect_ratio": avg_aspect_ratio,
            "avg_height": np.mean(heights),
            "num_frames": len(sequence),
            "proximity": self._compute_proximity(bboxes, other_tracks)
        }

    def _compute_proximity(
        self,
        bboxes: List[List[int]],
        other_tracks: Optional[List[int]]
    ) -> float:
        """Computa proximidade média com outros animais"""
        if not other_tracks or len(bboxes) == 0:
            return 0.0

        # Simplificação: retornar distância média do centro
        centers = [(b[0] + b[2]) / 2 for b in bboxes]
        if len(centers) < 2:
            return 0.0

        distances = []
        for i in range(len(centers) - 1):
            distances.append(abs(centers[i + 1] - centers[i]))

        return np.mean(distances) if distances else 0.0

    def _empty_features(self) -> Dict:
        """Features vazias para estado inicial"""
        return {
            "motion_energy": 0,
            "motion_variance": 0,
            "direction_consistency": 0,
            "height_consistency": 1,
            "avg_aspect_ratio": 1,
            "avg_height": 0,
            "num_frames": 0,
            "proximity": 0
        }

    def _classify_ml(self, features: Dict) -> Tuple[Behavior, float]:
        """Classificação usando modelo ML"""
        # Implementação futura quando modelo estiver disponível
        return self._classify_heuristic(features)

    def _classify_heuristic(self, features: Dict) -> Tuple[Behavior, float]:
        """Classificação heurística baseada em regras"""
        scores = {b: 0.0 for b in Behavior}

        # Score para CALMO
        if features["motion_energy"] < 0.1 * features["num_frames"]:
            scores[Behavior.CALMO] += 0.6
        if features["height_consistency"] > 0.8:
            scores[Behavior.CALMO] += 0.2

        # Score para AGITADO
        if features["motion_energy"] > 0.5 * features["num_frames"]:
            scores[Behavior.AGITADO] += 0.7
        if features["motion_variance"] > 0.3:
            scores[Behavior.AGITADO] += 0.3

        # Score para ALIMENTANDO
        if features["avg_aspect_ratio"] > 1.2:  # Mais largo que alto
            scores[Behavior.ALIMENTANDO] += 0.5
        if features["height_consistency"] > 0.7:
            scores[Behavior.ALIMENTANDO] += 0.2

        # Score para CAMINHANDO
        if features["direction_consistency"] > 0.7:
            scores[Behavior.CAMINHANDO] += 0.6
        if 0.15 < features["motion_energy"] / features["num_frames"] < 0.5:
            scores[Behavior.CAMINHANDO] += 0.3

        # Score para DEITADO
        if features["avg_height"] < 0.3:  # Altura reduzida
            scores[Behavior.DEITADO] += 0.7
        if features["motion_energy"] < 0.15 * features["num_frames"]:
            scores[Behavior.DEITADO] += 0.2

        # Score para INTERAGINDO
        if features["proximity"] < 50:  # Perto de outros
            scores[Behavior.INTERAGINDO] += 0.5

        # Normalizar scores
        total = sum(scores.values())
        if total > 0:
            for k in scores:
                scores[k] /= total

        # Encontrar melhor comportamento
        best_behavior = max(scores, key=scores.get)
        confidence = scores[best_behavior]

        return best_behavior, min(0.99, confidence)

    def classify_frame(
        self,
        tracked_animals: List,
        frame_num: int
    ) -> Dict[int, Tuple[Behavior, float]]:
        """
        Classifica comportamento de todos animais no frame.

        Args:
            tracked_animals: Lista de animais rastreados
            frame_num: Número do frame atual

        Returns:
            Dict mapeando track_id -> (Behavior, confiança)
        """
        results = {}

        for animal in tracked_animals:
            track_id = animal.track_id if hasattr(animal, 'track_id') else animal.get('id')

            # Criar sequências dummy para demonstração
            dummy_frames = [np.zeros((480, 640, 3)) for _ in range(5)]
            dummy_bboxes = [animal.bbox if hasattr(animal, 'bbox') else animal.get('bbox', [100, 100, 200, 200]) for _ in range(5)]

            behavior, confidence = self.classify(
                track_id,
                dummy_frames,
                dummy_bboxes
            )

            results[track_id] = (behavior, confidence)

        return results

    def reset(self, track_id: Optional[int] = None):
        """Reseta buffers de sequência"""
        if track_id is not None:
            self.sequence_buffers.pop(track_id, None)
        else:
            self.sequence_buffers.clear()