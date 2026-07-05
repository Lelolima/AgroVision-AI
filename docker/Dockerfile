# Dockerfile para AgroVision AI
# Build: docker build -t agrovision:latest -f docker/Dockerfile .

FROM python:3.10-slim

# Configuracoes de ambiente
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependencias do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libglib2.0-0 \
    libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# Definir diretorio de trabalho
WORKDIR /app

# Copiar requirements primeiro para cache
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copiar codigo fonte
COPY . .

# Criar diretorio de modelos
RUN mkdir -p /app/agrovision/models/weights /app/logs

# Setar permissoes
RUN chmod +x scripts/*.py 2>/dev/null || true

# Expor porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Comando de inicializacao
CMD ["python", "-m", "agrovision.api.app"]