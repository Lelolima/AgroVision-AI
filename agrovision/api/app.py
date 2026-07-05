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

# CORS middleware - configurável por ambiente
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"],
    allow_credentials=True,
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
        }
    }


@app.post("/api/upload/video")
async def upload_video(file: UploadFile = File(...)):
    """Upload de vídeo para análise"""
    from agrovision.utils.video import process_video

    if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
        raise HTTPException(status_code=400, detail="Formato de vídeo não suportado")

    # Validar tamanho (max 500MB)
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)

    if size > 500 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Vídeo muito grande (max 500MB)")

    # Processar vídeo
    try:
        result = await process_video(file, detector, tracker)
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


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
                detections = detector.detect(data.get("frame"))
                await websocket.send_json({
                    "status": "processed",
                    "detections": detections
                })
    except WebSocketDisconnect:
        logger.info("Cliente WebSocket desconectado")


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agrovision.api.app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )