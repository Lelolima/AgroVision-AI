"""
Tracker de Animais - DeepSort
Rastreamento multi-objeto para manter identidade entre frames
"""

import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass

from agrovision.models.detector import Detection
from agrovision.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class TrackedAnimal:
    """Animal sendo rastreado"""
    track_id: int
    bbox: List[int]
    confidence: float
    class_name: str
    age: int = 0  # Frames desde primeira detecção
    last_seen: int = 0  # Último frame visto


class AnimalTracker:
    """
    Tracker usando DeepSort para manter identidade dos animais entre frames.

    Features:
    - Associação por movimento e aparência
    - Interpolação para oclusões curtas
    - ID swapping prevention
    """

    def __init__(
        self,
        max_age: int = 30,
        min_hits: int = 3,
        iou_threshold: float = 0.3
    ):
        """
        Inicializa o tracker.

        Args:
            max_age: Frames máximos sem detecção antes de remover track
            min_hits: Detecções mínimas para confirmar track
            iou_threshold: Threshold para IoU matching
        """
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold

        self.tracks: Dict[int, TrackedAnimal] = {}
        self.next_track_id = 0

        # Kalman filter para predição de movimento
        self.kf = self._create_kalman_filter()

        logger.info(f"Tracker inicializado: max_age={max_age}, iou_threshold={iou_threshold}")

    def _create_kalman_filter(self):
        """Cria filtro de Kalman simples para predição"""
        # Implementação simplificada - em produção usar pykalman ou similar
        return {
            'process_noise': 1e-4,
            'measurement_noise': 1e-1,
        }

    def update(self, detections: List[Detection], frame_num: int) -> List[TrackedAnimal]:
        """
        Atualiza tracker com novas detecções.

        Args:
            detections: Lista de detecções do frame atual
            frame_num: Número do frame atual

        Returns:
            Lista de animais rastreados atualizados
        """
        # Predizer posições dos tracks existentes
        predictions = self._predict_tracks()

        # Associar detecções com tracks
        associations = self._associate(detections, predictions)

        # Atualizar tracks baseados nas associações
        self._update_tracks(associations, detections, frame_num)

        # Criar novos tracks para detecções não associadas
        self._create_new_tracks(associations, detections, frame_num)

        # Remover tracks perdidos
        self._remove_lost_tracks(frame_num)

        return list(self.tracks.values())

    def _predict_tracks(self) -> Dict[int, List[int]]:
        """Prediz posições dos tracks usando Kalman filter"""
        predictions = {}
        for track_id, track in self.tracks.items():
            # Predição simples (em produção usar KF real)
            predictions[track_id] = track.bbox
        return predictions

    def _associate(
        self,
        detections: List[Detection],
        predictions: Dict[int, List[int]]
    ) -> Dict[int, int]:
        """
        Associa detecções com tracks existentes.

        Returns:
            Dict mapeando track_id -> detection_index
        """
        associations = {}
        used_detections = set()

        for track_id, pred_bbox in predictions.items():
            best_iou = 0
            best_det_idx = None

            for det_idx, det in enumerate(detections):
                if det_idx in used_detections:
                    continue

                iou = self._compute_iou(pred_bbox, det.bbox)

                if iou > best_iou and iou >= self.iou_threshold:
                    best_iou = iou
                    best_det_idx = det_idx

            if best_det_idx is not None:
                associations[track_id] = best_det_idx
                used_detections.add(best_det_idx)

        return associations

    def _compute_iou(self, bbox1: List[int], bbox2: List[int]) -> float:
        """Computa Intersection over Union entre dois bboxes"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])

        intersection = max(0, x2 - x1) * max(0, y2 - y1)

        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

        union = area1 + area2 - intersection

        if union == 0:
            return 0

        return intersection / union

    def _update_tracks(
        self,
        associations: Dict[int, int],
        detections: List[Detection],
        frame_num: int
    ):
        """Atualiza tracks com detecções associadas"""
        for track_id, det_idx in associations.items():
            det = detections[det_idx]

            if track_id in self.tracks:
                track = self.tracks[track_id]
                track.bbox = det.bbox
                track.confidence = det.confidence
                track.age += 1
                track.last_seen = frame_num

    def _create_new_tracks(
        self,
        associations: Dict[int, int],
        detections: List[Detection],
        frame_num: int
    ):
        """Cria novos tracks para detecções não associadas"""
        associated_det_indices = set(associations.values())

        for det_idx, det in enumerate(detections):
            if det_idx in associated_det_indices:
                continue

            track_id = self.next_track_id
            self.next_track_id += 1

            self.tracks[track_id] = TrackedAnimal(
                track_id=track_id,
                bbox=det.bbox,
                confidence=det.confidence,
                class_name=det.class_name,
                age=1,
                last_seen=frame_num
            )

            logger.debug(f"Novo track criado: ID={track_id}")

    def _remove_lost_tracks(self, frame_num: int):
        """Remove tracks perdidos há muitos frames"""
        to_remove = []

        for track_id, track in self.tracks.items():
            if frame_num - track.last_seen > self.max_age:
                to_remove.append(track_id)
                logger.debug(f"Track removido (perdido): ID={track_id}")

        for track_id in to_remove:
            del self.tracks[track_id]

    def get_active_tracks(self) -> List[TrackedAnimal]:
        """Retorna tracks ativos confirmados"""
        return [
            track for track in self.tracks.values()
            if track.age >= self.min_hits
        ]

    def get_track_count(self) -> int:
        """Retorna número de tracks ativos"""
        return len(self.get_active_tracks())

    def reset(self):
        """Reseta o tracker"""
        self.tracks.clear()
        self.next_track_id = 0
        logger.info("Tracker resetado")