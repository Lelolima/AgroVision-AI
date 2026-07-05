# Documentação Técnica - AgroVision AI

## Visão Geral

AgroVision AI é um sistema de monitoramento pecuário baseado em visão computacional que fornece:

- **Detecção de animais** em tempo real usando YOLOv5
- **Rastreamento multi-objeto** com DeepSort
- **Estimativa de peso** baseada em dimensões corporais (LightGBM)
- **Classificação de comportamento** usando CNN 3D ou heurísticas

---

## Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        Camada de API                            │
│                     FastAPI (app.py, routes.py)                 │
│                                                                 │
│         Dashboard Web ←→ Endpoints REST ←→ WebSocket           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      Camada de Modelos                          │
│  ┌───────────┐ ┌───────────┐ ┌───────────────┐ ┌────────────┐  │
│  │ Detector  │ │ Tracker   │ │ Weight Est.   │ │ Behavior   │  │
│  │ (YOLOv5)  │ │ (DeepSort)│ │ (LightGBM)    │ │ (CNN 3D)   │  │
│  └───────────┘ └───────────┘ └───────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Camada de Utilitários                       │
│  ┌───────────────────┐ ┌───────────────────┐ ┌──────────────┐  │
│  │ process_video.py  │ │ logger.py         │ │ database.py  │  │
│  └───────────────────┘ └───────────────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       Infraestrutura                            │
│  SQLite (local) ↔ PostgreSQL (produção) ↔ S3 (armazenamento)  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Estrutura de Diretórios

```
AgroVision-AI/
├── agrovision/              # Pacote principal
│   ├── __init__.py
│   ├── api/                 # API FastAPI
│   │   ├── __init__.py
│   │   ├── app.py          # Aplicação principal
│   │   └── routes.py       # Rotas da API
│   ├── models/             # Modelos de ML
│   │   ├── __init__.py
│   │   ├── detector.py     # Detecção YOLO
│   │   ├── tracker.py      # Tracking DeepSort
│   │   ├── weight_estimator.py
│   │   └── behavior_classifier.py
│   ├── utils/              # Utilitários
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── video.py
│   └── config/             # Configurações
│       ├── __init__.py
│       └── settings.py
├── web/                    # Frontend
│   ├── index.html
│   ├── css/
│   │   └── styles.css
│   └── js/
│       └── dashboard.js
├── scripts/
│   └── download_models.py
├── tests/
│   └── test_api.py
├── docker/
│   ├── Dockerfile
│   └── nginx.conf
├── docs/
│   └── CORRECOES_REALIZADAS.md
├── requirements.txt
├── setup.py
├── docker-compose.yml
└── README.md
```

---

## Instalação

### Pré-requisitos

- Python 3.9 ou superior
- pip 21.0+
- (Opcional) NVIDIA GPU com CUDA 11.7+

### Passo a Passo

1. **Clonar repositório**
```bash
git clone https://github.com/Lelolima/AgroVision-AI.git
cd AgroVision-AI
```

2. **Criar ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
```

4. **Baixar modelos**
```bash
python scripts/download_models.py
```

5. **Configurar ambiente**
```bash
cp .env.example .env
# Editar .env conforme necessário
```

6. **Executar testes**
```bash
pytest tests/ -v
```

7. **Iniciar servidor**
```bash
python -m agrovision.api.app
```

---

## Uso da API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Upload de Vídeo
```bash
curl -X POST http://localhost:8000/api/upload/video \
  -F "file=@video.mp4"
```

### WebSocket para Detecção em Tempo Real
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/detect');

ws.onopen = () => {
  ws.send(JSON.stringify({
    action: 'subscribe',
    topic: 'detections'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Detecções:', data.detections);
};
```

---

## Configurações

Veja `.env.example` para todas as opções:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| HOST | Host do servidor | 0.0.0.0 |
| PORT | Porta do servidor | 8000 |
| DEBUG | Modo debug | True |
| MODEL_DIR | Diretório dos modelos | ./agrovision/models/weights |
| YOLO_MODEL | Modelo YOLO | yolov5s.pt |
| CONFIDENCE_THRESHOLD | Threshold de confiança | 0.5 |
| MAX_VIDEO_SIZE_MB | Tamanho máximo de upload | 500 |
| DATABASE_URL | URL do banco de dados | sqlite:///./agrovision.db |
| LOG_LEVEL | Nível de log | INFO |
| EDGE_MODE | Modo edge device | False |

---

## Deploy com Docker

### Produção

```bash
# Build das imagens
docker-compose build

# Iniciar serviços
docker-compose up -d

# Ver logs
docker-compose logs -f

# Parar serviços
docker-compose down
```

### URLs de Acesso

| Serviço | URL |
|---------|-----|
| API | http://localhost:8000 |
| Dashboard | http://localhost:8000 |
| Web (nginx) | http://localhost |
| PostgreSQL | localhost:5432 |

---

## Modelo de Dados

### Detection
```python
@dataclass
class Detection:
    bbox: List[int]        # [x1, y1, x2, y2]
    confidence: float      # 0.0 - 1.0
    class_id: int          # ID da classe
    class_name: str        # Nome da classe
    track_id: int          # ID do track (após tracking)
    weight_est: float      # Peso estimado (kg)
    behavior: str          # Comportamento detectado
```

### TrackedAnimal
```python
@dataclass
class TrackedAnimal:
    track_id: int
    bbox: List[int]
    confidence: float
    class_name: str
    age: int               # Frames desde primeira detecção
    last_seen: int         # Último frame visto
```

---

## Comportamentos Suportados

| Comportamento | Descrição | Características |
|---------------|-----------|-----------------|
| calmo | Animal parado ou movimento mínimo | Baixa energia de movimento |
| agitado | Movimento rápido e errático | Alta energia, direção inconsistente |
| alimentando | Cabeça baixa, movimento consistente | Ratio de aspecto específico |
| caminhando | Direção consistente | Constância de direção > 0.7 |
| deitado | Altura reduzida, imóvel | Height ratio < 0.5 |
| interagindo | Proximidade com outros animais | Distância < 50px de outros |

---

## Troubleshooting

### Modelo YOLO não carrega
```bash
# Verificar se ultralytics está instalado
pip show ultralytics

# Reinstalar se necessário
pip install --upgrade ultralytics

# Executar download manual
python scripts/download_models.py
```

### Erro de CUDA/GPU
```bash
# Verificar se CUDA está disponível
python -c "import torch; print(torch.cuda.is_available())"

# Forçar modo CPU
export CUDA_VISIBLE_DEVICES=""
```

### Dashboard não carrega
```bash
# Verificar se API está rodando
curl http://localhost:8000/api/health

# Verificar logs
docker-compose logs agrovision-api
```

---

## Performance

### Benchmarks (RTX 3080)

| Resolução | FPS | Latência |
|-----------|-----|----------|
| 640x480 | 45 | 22ms |
| 1280x720 | 28 | 35ms |
| 1920x1080 | 15 | 67ms |

### Otimizações para Edge

```bash
# Habilitar modo edge
export EDGE_MODE=true
export QUANTIZE_MODELS=true

# Usar ONNX Runtime
pip install onnxruntime-gpu
```

---

## Testes

```bash
# Todos os testes
pytest tests/ -v

# Com coverage
pytest tests/ -v --cov=agrovision --cov-report=html

# Teste específico
pytest tests/test_api.py::test_health_check -v
```

---

## Contribuição

1. Fork o repositório
2. Crie branch para feature (`git checkout -b feature/nova-feature`)
3. Commit mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra Pull Request

---

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

---

## Suporte

- Issues: https://github.com/Lelolima/AgroVision-AI/issues
- Email: contato@agrovision.ai
- Documentação: https://agrovision.ai/docs