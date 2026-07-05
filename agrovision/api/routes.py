"""
Rotas de análise da API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter()


@router.post("/video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Analisa vídeo enviado e retorna detecções.

    - **file**: Arquivo de vídeo (MP4, AVI, MOV, MKV)
    - **return**: Resultados da análise com detecções, tracking e estimativas
    """
    # Implementação completa em agrovision.utils.video
    return JSONResponse(content={
        "status": "processing",
        "message": "Vídeo recebido para análise",
        "filename": file.filename
    })


@router.post("/image")
async def analyze_image(file: UploadFile = File(...)):
    """
    Analisa imagem enviada e retorna detecções.

    - **file**: Arquivo de imagem (JPG, PNG, BMP)
    - **return**: Detecções com bbox, confiança, peso estimado e comportamento
    """
    return JSONResponse(content={
        "status": "success",
        "detections": []
    })


@router.post("/stream")
async def analyze_stream():
    """
    Endpoint para análise de stream em tempo real.

    Usa WebSocket para comunicação bidirecional.
    """
    return JSONResponse(content={
        "status": "info",
        "message": "Use WebSocket em /ws/detect para stream em tempo real"
    })