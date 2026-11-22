"""
AgroVision AI - API Principal
FastAPI application para análise de vídeos e imagens pecuárias
"""

import os
import sys
from pathlib import Path
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from agrovision.api.routes import analysis_router, results_router
from agrovision.utils.logger import setup_logger
from agrovision.config.settings import settings

# Setup logging
logger = setup_logger(__name__)

# Import models lazy to avoid circular imports
detector = None
tracker = None
weight_estimator = None
behavior_classifier = None


async def load_models():
    """Carrega modelos ML de forma lazy"""
    global detector, tracker, weight_estimator, behavior_classifier

    try:
        from agrovision.models.detector import AnimalDetector
        detector = AnimalDetector()
        logger.info("Detector YOLO carregado com sucesso")
    except Exception as e:
        logger.warning(f"Detector indisponível: {e}. Usando modo simulação.")
        detector = None

    try:
        from agrovision.models.tracker import AnimalTracker
        tracker = AnimalTracker()
        logger.info("Tracker DeepSort carregado com sucesso")
    except Exception as e:
        logger.warning(f"Tracker indisponível: {e}")
        tracker = None

    try:
        from agrovision.models.weight_estimator import WeightEstimator
        weight_estimator = WeightEstimator()
    except Exception as e:
        logger.warning(f"Estimador de peso indisponível: {e}")
        weight_estimator = None

    try:
        from agrovision.models.behavior_classifier import BehaviorClassifier
        behavior_classifier = BehaviorClassifier(use_heuristics=True)
    except Exception as e:
        logger.warning(f"Classificador de comportamento indisponível: {e}")
        behavior_classifier = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciamento de lifecycle da aplicação"""
    logger.info("Iniciando AgroVision AI API...")
    await load_models()
    yield
    logger.info("Fechando AgroVision AI API...")


app = FastAPI(
    title="AgroVision AI",
    description="Sistema de Monitoramento Pecuário Inteligente",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware - configurável por ambiente.
# Com origem "*" não enviamos credenciais (combinação inválida e insegura).
_cors_any = settings.ALLOWED_ORIGINS.strip() == "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_any else [o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=not _cors_any,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Mount static files
web_dir = Path(__file__).parent.parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Dashboard web com SVGs animados"""
    index_path = web_dir / "index.html"
    if index_path.exists():
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>AgroVision AI - Dashboard em construção</h1>")


@app.get("/api/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "models": {
            "detector": "loaded" if detector else "unloaded",
            "tracker": "loaded" if tracker else "unloaded",
            "weight_estimator": "loaded" if weight_estimator else "unloaded",
            "behavior_classifier": "loaded" if behavior_classifier else "unloaded",
        },
        "simulation_mode": bool(detector is None or getattr(detector, "simulate", False)),
    }


@app.post("/api/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload de vídeo para análise"""
    from agrovision.utils.video import process_video

    if not (file.filename or "").lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Formato de vídeo não suportado")

    # Validar tamanho (MAX_VIDEO_SIZE_MB)
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)

    max_mb = settings.MAX_VIDEO_SIZE_MB
    if size > max_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"Vídeo muito grande (max {max_mb}MB)")

    # Processar vídeo
    try:
        result = await process_video(
            file, detector, tracker, weight_estimator, behavior_classifier,
            frame_skip=settings.FRAME_SKIP,
        )
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail="Erro no processamento do vídeo")
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    result["simulated"] = bool(detector is not None and getattr(detector, "simulate", False))
    return JSONResponse(content=jsonable_encoder(result))


@app.websocket("/ws/detect")
async def websocket_detect(websocket: WebSocket):
    """WebSocket para detecção em tempo real"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if detector is None:
                # Modo simulação
                await websocket.send_json({
                    "status": "simulated",
                    "detections": generate_simulated_detections()
                })
            else:
                # Processamento real
                frame = _decode_ws_frame(data.get("frame"))
                if frame is None:
                    await websocket.send_json({
                        "status": "error",
                        "detail": "frame inválido (esperado JPEG/PNG em base64)",
                    })
                    continue
                detections = detector.detect(frame)
                await websocket.send_json({
                    "status": "simulated" if getattr(detector, "simulate", False) else "processed",
                    "detections": jsonable_encoder(detections),
                })
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")


def _decode_ws_frame(frame_b64):
    """Decodifica frame base64 (JPEG/PNG, opcionalmente data URL) em array BGR; None se inválido."""
    import base64
    import binascii

    import cv2
    import numpy as np

    if not isinstance(frame_b64, str) or not frame_b64:
        return None
    if frame_b64.startswith("data:") and "," in frame_b64:
        frame_b64 = frame_b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(frame_b64, validate=True)
    except (binascii.Error, ValueError):
        return None
    if not raw:
        return None
    return cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)


def generate_simulated_detections():
    """Gera detecções simuladas para demonstração"""
    import random
    import time

    return {
        "timestamp": time.time(),
        "animals": [
            {
                "id": i,
                "bbox": [
                    random.randint(50, 500),
                    random.randint(50, 300),
                    random.randint(80, 150),
                    random.randint(60, 120)
                ],
                "confidence": random.uniform(0.85, 0.99),
                "weight_est": random.randint(100, 200),
                "behavior": random.choice(["calmo", "agitado", "alimentando"])
            }
            for i in range(random.randint(1, 5))
        ],
        "total_count": random.randint(1, 5),
        "avg_weight": random.randint(110, 170)
    }


# Include routers
app.include_router(analysis_router, prefix="/api/analyze", tags=["Análise"])
app.include_router(results_router, prefix="/api/results", tags=["Resultados"])


def main():
    """Entry point do console script ``agrovision`` (setup.py)."""
    import uvicorn
    uvicorn.run(
        "agrovision.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agrovision.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )