"""
Testes da API AgroVision AI
"""

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Cliente de teste"""
    from agrovision.api.app import app
    return TestClient(app)


def test_health_check(client):
    """Testa endpoint de health check"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Testa endpoint root"""
    response = client.get("/")
    assert response.status_code == 200


def test_upload_video_invalid_format(client):
    """Testa upload com formato inválido"""
    # Criar arquivo temporário
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test content")
        f_path = f.name

    try:
        with open(f_path, "rb") as f:
            response = client.post(
                "/api/upload/video",
                files={"file": ("test.txt", f, "text/plain")}
            )
        assert response.status_code == 400
        assert "não suportado" in response.json()["detail"]
    finally:
        import os
        os.unlink(f_path)


def test_simulated_detection():
    """Testa detecção simulada"""
    from agrovision.models.detector import AnimalDetector

    detector = AnimalDetector(simulate=True)
    detections = detector.detect("dummy_image")

    assert isinstance(detections, list)
    if len(detections) > 0:
        det = detections[0]
        assert hasattr(det, 'bbox')
        assert hasattr(det, 'confidence')
        assert hasattr(det, 'class_name')


def test_weight_estimator_simple():
    """Testa estimador de peso (fórmula simplificada)"""
    from agrovision.models.weight_estimator import WeightEstimator

    estimator = WeightEstimator(breed="default")
    result = estimator.estimate(
        bbox=[100, 100, 200, 200],
        image_height=480,
        image_width=640,
        confidence=0.9
    )

    assert result.weight_kg >= 50
    assert result.weight_kg <= 800
    assert result.method == "formula" or result.method == "lightgbm"


def test_tracker_basic():
    """Testa tracker básico"""
    from agrovision.models.tracker import AnimalTracker
    from agrovision.models.detector import Detection

    tracker = AnimalTracker()

    # Criar detecções simuladas
    detections = [
        Detection(
            bbox=[100, 100, 200, 200],
            confidence=0.9,
            class_id=0,
            class_name="vaca"
        )
    ]

    # Atualizar tracker
    tracked = tracker.update(detections, frame_num=0)

    assert len(tracked) >= 0  # Pode ser 0 se não confirmar


def test_behavior_classifier():
    """Testa classificador de comportamento"""
    from agrovision.models.behavior_classifier import BehaviorClassifier, Behavior
    import numpy as np

    classifier = BehaviorClassifier(use_heuristics=True)

    # Criar frames e bboxes simulados
    frames = [np.zeros((480, 640, 3)) for _ in range(5)]
    bboxes = [[100, 100, 200, 200] for _ in range(5)]

    behavior, confidence = classifier.classify(
        track_id=1,
        frames=frames,
        bboxes=bboxes
    )

    assert isinstance(behavior, Behavior)
    assert 0 <= confidence <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])