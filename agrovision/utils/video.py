"""
Processamento de vídeo
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any
import tempfile
import asyncio

from agrovision.utils.logger import setup_logger

logger = setup_logger(__name__)


async def process_video(
    file,
    detector=None,
    tracker=None,
    weight_estimator=None,
    behavior_classifier=None,
    frame_skip: int = 1
) -> Dict[str, Any]:
    """
    Processa vídeo e extrai informações dos animais.

    Args:
        file: UploadFile ou caminho do vídeo
        detector: Instância de AnimalDetector
        tracker: Instância de AnimalTracker
        weight_estimator: Instância de WeightEstimator
        behavior_classifier: Instância de BehaviorClassifier
        frame_skip: Pular frames para processamento mais rápido

    Returns:
        Dict com resultados da análise
    """
    # Salvar vídeo temporariamente
    if hasattr(file, 'filename'):
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            content = await file.read()
            tmp.write(content)
            video_path = tmp.name
    else:
        video_path = str(file)

    results = {
        # antes: "video_path" expunha o caminho temporário do servidor
        "filename": Path(getattr(file, "filename", None) or video_path).name,
        "frames_processed": 0,
        "detections": [],
        "tracks": [],
        "summary": {}
    }

    try:
        # Abrir vídeo
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"Não foi possível abrir o vídeo: {video_path}")

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        logger.info(f"Vídeo: {frame_count} frames, {fps} FPS, {width}x{height}")

        frame_num = 0
        all_detections = []
        all_tracks = {}

        while True:
            ret, frame = cap.read()

            if not ret:
                break

            if frame_num % (frame_skip + 1) != 0:
                frame_num += 1
                continue

            # Detectar
            if detector:
                detections = detector.detect(frame)
            else:
                detections = []

            # Trackear
            if tracker:
                tracked = tracker.update(detections, frame_num)
                for t in tracked:
                    all_tracks[t.track_id] = t
            else:
                tracked = []

            # Estimar peso e classificar comportamento
            for t in tracked:
                if weight_estimator:
                    weight = weight_estimator.estimate(
                        t.bbox, height, width, t.confidence
                    )
                    t.weight_est = weight.weight_kg

                if behavior_classifier:
                    behavior, conf = behavior_classifier.classify(
                        t.track_id,
                        [frame],
                        [t.bbox]
                    )
                    t.behavior = behavior.value

            all_detections.append({
                "frame": frame_num,
                "detections": len(detections),
                "tracks": len(tracked)
            })

            results["frames_processed"] += 1
            frame_num += 1

            # Limite de processamento (primeiros 100 frames)
            if results["frames_processed"] >= 100:
                break

        cap.release()

        # Gerar resumo
        results["summary"] = {
            "total_frames": results["frames_processed"],
            "unique_animals": len(all_tracks),
            "avg_animals_per_frame": np.mean([d["tracks"] for d in all_detections]) if all_detections else 0,
            "max_animals": max([d["tracks"] for d in all_detections]) if all_detections else 0,
            "video_info": {
                "fps": fps,
                "width": width,
                "height": height
            }
        }

        results["tracks"] = [
            {
                "track_id": t.track_id,
                "first_seen": t.age,
                "last_bbox": t.bbox,
                "weight_est": getattr(t, "weight_est", None),
                "behavior": getattr(t, "behavior", None)
            }
            for t in all_tracks.values()
        ]

        logger.info(f"Processamento concluído: {results['summary']['unique_animals']} animais únicos")

    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        results["error"] = str(e)
    finally:
        # Limpar arquivo temporário
        if video_path:
            try:
                Path(video_path).unlink()
            except Exception as e:
                logger.warning(f"Erro ao remover arquivo temporário: {e}")

    return results


def extract_keyframes(
    video_path: str,
    output_dir: str,
    interval_seconds: int = 5
) -> List[str]:
    """
    Extrai keyframes do vídeo em intervalos regulares.

    Args:
        video_path: Caminho do vídeo
        output_dir: Diretório para salvar frames
        interval_seconds: Intervalo entre frames em segundos

    Returns:
        Lista de caminhos dos frames extraídos
    """
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    interval_frames = fps * interval_seconds

    frames = []
    frame_num = 0
    saved_num = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_num % interval_frames == 0:
            output_path = Path(output_dir) / f"frame_{saved_num:04d}.jpg"
            cv2.imwrite(str(output_path), frame)
            frames.append(str(output_path))
            saved_num += 1

        frame_num += 1

    cap.release()
    return frames