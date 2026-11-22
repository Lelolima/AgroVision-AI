"""
Testes de regressão da auditoria 2026-11-22 (imagens/vídeos sintéticos, sem pesos YOLO).
"""

import base64
import os
import tempfile
from types import SimpleNamespace

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from agrovision.api.app import app

    # "with" executa o lifespan (carrega modelos; sem pesos -> modo simulação)
    with TestClient(app) as c:
        yield c


def _png_bytes():
    ok, buf = cv2.imencode(".png", np.full((120, 160, 3), 90, dtype=np.uint8))
    assert ok
    return buf.tobytes()


def _synthetic_video(frames=5):
    fd, path = tempfile.mkstemp(suffix=".avi")
    os.close(fd)
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"MJPG"), 5, (160, 120))
    for i in range(frames):
        frame = np.zeros((120, 160, 3), dtype=np.uint8)
        cv2.rectangle(frame, (10 + i * 5, 30), (60 + i * 5, 80), (200, 200, 200), -1)
        writer.write(frame)
    writer.release()
    return path


def test_routes_exports_routers():
    """Antes: app.py importava analysis_router/results_router inexistentes -> API não iniciava."""
    from agrovision.api.routes import analysis_router, results_router

    assert analysis_router is not None and results_router is not None


def test_health_reports_simulation_mode(client):
    data = client.get("/api/health").json()
    assert data["simulation_mode"] is True  # sem pesos YOLO no repositório
    assert data["models"]["weight_estimator"] == "loaded"


def test_image_endpoint_flags_simulated_results(client):
    r = client.post("/api/analyze/image", files={"file": ("a.png", _png_bytes(), "image/png")})
    assert r.status_code == 200
    body = r.json()
    assert body["simulated"] is True
    for det in body["detections"]:
        x1, y1, x2, y2 = det["bbox"]
        assert x2 > x1 and y2 > y1


def test_image_endpoint_rejects_invalid_image(client):
    r = client.post("/api/analyze/image", files={"file": ("a.png", b"xx", "image/png")})
    assert r.status_code == 400


def test_video_upload_processes_synthetic_video(client):
    path = _synthetic_video()
    try:
        with open(path, "rb") as fh:
            r = client.post("/api/upload/video", files={"file": ("v.avi", fh, "video/x-msvideo")})
    finally:
        os.unlink(path)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["simulated"] is True
    assert body["frames_processed"] == 3  # FRAME_SKIP=1 (padrão): frames 0, 2, 4
    assert "video_path" not in body  # não expõe caminho do servidor


def test_video_upload_corrupt_returns_422(client):
    r = client.post("/api/upload/video", files={"file": ("v.mp4", b"not a video", "video/mp4")})
    assert r.status_code == 422


def test_websocket_rejects_invalid_frame_when_detector_real(client, monkeypatch):
    from agrovision.api import app as app_module

    fake = SimpleNamespace(simulate=False, detect=lambda frame: [])
    monkeypatch.setattr(app_module, "detector", fake)
    with client.websocket_connect("/ws/detect") as ws:
        ws.send_json({"frame": "%%%"})
        assert ws.receive_json()["status"] == "error"
        ok, buf = cv2.imencode(".jpg", np.zeros((10, 10, 3), dtype=np.uint8))
        ws.send_json({"frame": base64.b64encode(buf.tobytes()).decode()})
        assert ws.receive_json() == {"status": "processed", "detections": []}


def test_simulated_bbox_is_xyxy():
    from agrovision.models.detector import AnimalDetector

    det = AnimalDetector(simulate=True)
    for _ in range(20):
        for d in det.detect(None):
            assert d.bbox[2] > d.bbox[0] and d.bbox[3] > d.bbox[1]


def test_class_name_uses_model_names():
    """Antes: YOLO COCO classe 0 ('person') virava 'vaca'."""
    from agrovision.models.detector import AnimalDetector

    det = AnimalDetector(simulate=True)
    result = SimpleNamespace(names={0: "person", 19: "cow"})
    assert det._class_name(result, 0) == "person"
    assert det._class_name(result, 19) == "vaca"
    assert det._class_name(SimpleNamespace(names=None), 1) == "bezerro"


def test_angus_breed_coefficients_used():
    """Antes: chave 'angu s' fazia 'angus' cair no coeficiente default."""
    from agrovision.models.weight_estimator import WeightEstimator

    e = WeightEstimator(breed="angus")
    assert e.get_breed_info()["coefficients"] == WeightEstimator.BREED_COEFFICIENTS["angus"]
