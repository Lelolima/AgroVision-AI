"""
Configurações do sistema
Centraliza todas as configurações e variáveis de ambiente
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # API
    HOST: str = Field(default="0.0.0.0", description="Host do servidor")
    PORT: int = Field(default=8000, description="Porta do servidor")
    DEBUG: bool = Field(default=True, description="Modo debug")

    # CORS
    ALLOWED_ORIGINS: str = Field(
        default="*",
        description="Origins permitidas (separadas por vírgula)"
    )

    # Modelos
    _model_dir: Optional[Path] = None

    @property
    def MODEL_DIR(self) -> Path:
        if self._model_dir is None:
            self._model_dir = Path(__file__).parent.parent / "models" / "weights"
            self._model_dir.mkdir(parents=True, exist_ok=True)
        return self._model_dir

    YOLO_MODEL: str = Field(default="yolov5s.pt", description="Modelo YOLO")
    TRACKER_MODEL: str = Field(default="deepsort", description="Modelo de tracking")

    # Processamento de vídeo
    MAX_VIDEO_SIZE_MB: int = Field(default=500, description="Tamanho máximo de vídeo (MB)")
    FRAME_SKIP: int = Field(default=1, description="Pular frames no processamento")
    CONFIDENCE_THRESHOLD: float = Field(default=0.5, description="Threshold de confiança")

    # Banco de dados
    DATABASE_URL: str = Field(
        default="sqlite:///./agrovision.db",
        description="URL de conexão do banco de dados"
    )
    DB_ECHO: bool = Field(default=False, description="Log de queries SQL")

    # Edge computing
    EDGE_MODE: bool = Field(default=False, description="Modo edge device")
    QUANTIZE_MODELS: bool = Field(default=False, description="Quantização de modelos")

    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Nível de log")
    LOG_FILE: Path = Field(default=Path("./logs/agrovision.log"), description="Arquivo de log")

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = Field(default=30, description="Intervalo de heartbeat (s)")

    # AWS S3 (opcional)
    AWS_ACCESS_KEY: str = Field(default="", description="AWS Access Key")
    AWS_SECRET_KEY: str = Field(default="", description="AWS Secret Key")
    S3_BUCKET: str = Field(default="", description="S3 Bucket")


# Singleton
settings = Settings()


def get_settings() -> Settings:
    """Retorna a instância singleton de configurações"""
    return settings