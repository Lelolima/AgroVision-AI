"""
Rotas de análise da API
"""

from dataclasses import asdict

import cv2
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

analysis_router = APIRouter()
# Rotas de resultados persistidos ainda não implementadas (não há banco de dados no código atual).
results_router = APIRouter()

# Compatibilidade com o nome antigo
router = analysis_router

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp")


def _app_module():
    from agrovision.api import app as app_module

    return app_module


@analysis_router.post("/video")
async def analyze_video(file: UploadFile = File(...)):
    """Analisa vídeo enviado (mesmo pipeline de /api/upload/video)."""
    return await _app_module().upload_video(file)


@analysis_router.post("/image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analisa imagem enviada e retorna detecções.

    O campo ``simulated`` indica se as detecções vieram do modo simulação
    (sem pesos YOLO disponíveis) — nesse caso NÃO são detecções reais.
    """
    if not (file.filename or "").lower().endswith(IMAGE_EXTENSIONS):
        raise HTTPException(status_code=400, detail="Formato de imagem não suportado")

    data = await file.read()
    image = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR) if data else None
    if image is None:
        raise HTTPException(status_code=400, detail="Imagem inválida ou corrompida")

    m = _app_module()
    detector = m.detector
    if detector is None:
        return JSONResponse(content={"status": "unavailable", "simulated": False, "detections": []})

    detections = detector.detect(image)
    h, w = image.shape[:2]
    out = []
    for det in detections:
        item = asdict(det)
        if m.weight_estimator is not None:
            est = m.weight_estimator.estimate(det.bbox, h, w, det.confidence)
            item["weight_est"] = est.weight_kg
            item["weight_method"] = est.method
        out.append(item)

    return JSONResponse(content={
        "status": "success",
        "simulated": bool(getattr(detector, "simulate", False)),
        "detections": out,
    })


@analysis_router.post("/stream")
async def analyze_stream():
    """
    Endpoint para análise de stream em tempo real.

    Usa WebSocket para comunicação bidirecional.
    """
    return JSONResponse(content={
        "status": "info",
        "message": "Use WebSocket em /ws/detect para stream em tempo real"
    })
