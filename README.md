# 🐄 AgroVision AI - Sistema de Monitoramento Pecuário Inteligente

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

Sistema de visão computacional para monitoramento de animais em ambientes agrícolas, com detecção, rastreamento, estimativa de peso e classificação de comportamento.

## 🚀 Funcionalidades

- **Detecção de Animais** - YOLOv5/Ultralytics para detecção em tempo real
- **Rastreamento Multi-Objeto** - DeepSort para tracking consistente entre frames
- **Estimativa de Peso** - Modelo LightGBM baseado em dimensões corporais
- **Classificação de Comportamento** - CNN 3D para identificar padrões (calmo, agitado, alimentando)
- **API REST** - FastAPI com endpoints para upload e análise de vídeos
- **Dashboard Web** - Interface com SVGs animados CSS mostrando processamento em tempo real
- **Edge-Ready** - Otimizado para dispositivos de borda com quantização opcional

## 📋 Pré-requisitos

- Python 3.10+ (validado em 3.11)
- NVIDIA GPU (opcional)
- Docker e Docker Compose (opcional)

## ⚠️ Modo simulação (leia antes de usar)

O repositório **não inclui pesos YOLO nem modelo de peso LightGBM**. Sem o arquivo indicado em
`YOLO_MODEL` (caminho relativo ao diretório de execução), o detector entra em **modo simulação**
e gera detecções **aleatórias**. Desde a auditoria de 2026-11-22 todas as respostas indicam isso:

- `GET /api/health` → `"simulation_mode": true`
- `POST /api/upload/video`, `POST /api/analyze/image` → `"simulated": true`
- WebSocket `/ws/detect` → `"status": "simulated"`

Sem `weight_model.pkl`, o peso é estimado por fórmula aproximada (`"weight_method": "formula"`).

## 🔧 Instalação

```bash
git clone https://github.com/Lelolima/AgroVision-AI.git
cd AgroVision-AI
python -m venv .venv && .venv\Scripts\activate     # Linux/macOS: source .venv/bin/activate

# CPU (recomendado para testes):
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements-dev.txt      # inclui requirements.txt + pytest/httpx/ruff
# Opcionais (não usados pelo código atual): pip install -r requirements-optional.txt
```

### Modelos (opcional, para detecção real)

```bash
python scripts/download_models.py   # baixa yolov5s.pt via ultralytics (requer internet)
```

Um YOLO pré-treinado em COCO detecta `cow`, `horse`, `sheep` etc.; os nomes vêm do próprio modelo
(traduzidos para `vaca`, `cavalo`, `ovelha`, `porco`). Classes fora disso aparecem com o nome original.

### Executar

```bash
python -m agrovision.api.app        # http://localhost:8000  (docs em /docs)
# ou: uvicorn agrovision.api.app:app --reload
```

## 🔑 Variáveis de ambiente

Lidas por `agrovision/config/settings.py` (arquivo `.env` opcional, veja `.env.example`):

| Variável | Padrão | Uso real |
|----------|--------|----------|
| `HOST`, `PORT`, `DEBUG` | `0.0.0.0`, `8000`, `True` | servidor (`python -m agrovision.api.app`) |
| `ALLOWED_ORIGINS` | `*` | CORS; com `*` as credenciais ficam desabilitadas |
| `YOLO_MODEL` | `yolov5s.pt` | caminho do peso YOLO |
| `CONFIDENCE_THRESHOLD` | `0.5` | limiar de detecção |
| `MAX_VIDEO_SIZE_MB` | `500` | limite de upload |
| `FRAME_SKIP` | `1` | frames pulados entre processamentos |

As demais (`DATABASE_URL`, `EDGE_MODE`, `AWS_*`, ...) existem em `Settings` mas não são usadas pelo código atual.

## 🌐 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Dashboard web estático |
| `/api/health` | GET | Health check + `simulation_mode` |
| `/api/upload/video` | POST | Processa até 100 frames do vídeo (detecção, tracking, peso, comportamento) |
| `/api/analyze/video` | POST | Igual a `/api/upload/video` |
| `/api/analyze/image` | POST | Detecção em uma imagem (JPG/PNG/BMP) |
| `/api/analyze/stream` | POST | Informativo: use o WebSocket |
| `/ws/detect` | WebSocket | Envie `{"frame": "<JPEG/PNG em base64>"}` |

`/api/results/{job_id}` **não está implementado** (não há persistência).

## 🖥️ Interface Web

Acesse o dashboard em `http://localhost:8000/` para visualizar:

- **Feed simulado** com cena de fazenda e vacas animadas
- **Contadores em tempo real**: total de animais, peso médio, comportamento dominante, tempo de sessão
- **Painel lateral** com lista de animais detectados com detalhes (ID, peso, comportamento)
- **Gráfico de atividade por hora**
- **Log de eventos** com histórico de detecções e alertas

### 📁 Estrutura do Diretório `web/`

```
web/
├── index.html                  # Dashboard principal
├── css/
│   └── styles.css            # Estilos CSS e animações
├── js/
│   └── dashboard.js          # Lógica JavaScript do dashboard (simulação em tempo real)
└── svg/                      # SVGs animados e documentação
    ├── README.md
    ├── index.html
    ├── dashboard-tempo-real.svg
    ├── deteccao-tempo-real.svg
    └── estatisticas-animadas.svg
```

### 🎨 Dashboard Principal (`web/index.html`)

Interface principal do sistema com:

- **Cabeçalho** com logo e status "Em Tempo Real"
- **Cards de estatísticas** (total de animais, peso médio, comportamento dominante, tempo de sessão)
- **Feed de vídeo simulado** com vacas se movendo em cena SVG
- **Painel lateral** com lista de animais detectados
- **Gráfico de atividade** e **log de eventos** na parte inferior

### 🎨 SVGs Animados (`web/svg/`)

O projeto inclui **3 SVGs animados** que demonstram visualmente as capacidades do sistema:

| Arquivo | Descrição | Animações |
|---------|-----------|-----------|
| `web/svg/dashboard-tempo-real.svg` | Dashboard completo com animais em pasto | • Caminhada dos animais (`animalWalk`)<br>• Scanning em tempo real (`scanMove`)<br>• Bounding boxes tracejadas (`bboxDash`)<br>• Indicadores de status (`pulse`)<br>• Gráfico de atividade animado (`barGrow`) |
| `web/svg/deteccao-tempo-real.svg` | Painel detalhado de detecção e tracking | • Bounding boxes com dash animado (`bboxDashMove`)<br>• Pulse para novas detecções (`newDetectionPulse`)<br>• Scanning vertical (`scanVertical`)<br>• Barras de confiança (`confidenceGrow`)<br>• Labels flutuantes (`labelFloat`) |
| `web/svg/estatisticas-animadas.svg` | Painel de estatísticas e métricas | • Contadores com pulse (`counterTick`)<br>• Gráfico de linha desenhando (`lineDraw`)<br>• Barras expandindo (`barExpand`)<br>• Gráfico de rosca preenchendo (`pieFill`)<br>• Elementos flutuantes (`float`) |

**Para visualizar:** Abra qualquer arquivo SVG diretamente no navegador, acesse `web/svg/index.html` para navegar entre eles, ou visualize via dashboard principal.

## 📊 Estrutura do Projeto

```
AgroVision-AI/
├── agrovision/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py          # API FastAPI
│   │   └── routes.py       # Rotas da API
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py     # Configurações
│   ├── models/
│   │   ├── __init__.py
│   │   ├── behavior_classifier.py  # Classificador de comportamento
│   │   ├── detector.py           # Detecção YOLO
│   │   ├── tracker.py          # Tracking DeepSort
│   │   └── weight_estimator.py  # Estimativa de peso
│   └── utils/
│       ├── __init__.py
│       ├── logger.py       # Logging estruturado
│       └── video.py        # Processamento de vídeo
├── web/
│   ├── index.html          # Dashboard principal
│   ├── css/
│   │   └── styles.css      # Estilos e animações
│   ├── js/
│   │   └── dashboard.js    # Lógica do dashboard
│   └── svg/
│       ├── README.md
│       ├── index.html
│       ├── dashboard-tempo-real.svg
│       ├── deteccao-tempo-real.svg
│       └── estatisticas-animadas.svg
├── scripts/
│   └── download_models.py  # Download de modelos
├── docker/
│   ├── Dockerfile          # Configuração Docker
│   └── nginx.conf
├── tests/
│   └── test_api.py         # Testes unitários
├── docs/
│   ├── CODE_REVIEW.md
│   ├── CORRECOES_APLICADAS.md
│   ├── CORRECOES_REALIZADAS.md
│   └── TECHNICAL_DOCUMENTATION.md
├── .env.example
├── .gitignore
├── GUIA_RAPIDO.txt
├── LICENSE
├── PROJETO_CONCLUIDO.md
├── README.md
├── demo.py
├── docker-compose.yml
├── requirements.txt
└── setup.py
```

## 🧪 Testes

```bash
python -m pytest -q                 # usa imagens/vídeos sintéticos; não requer GPU nem pesos
ruff check --select E9,F63,F7,F82 .
```

## 📝 Documentação

- [Documentação Técnica](docs/TECHNICAL_DOCUMENTATION.md)
- [Correções Realizadas](docs/CORRECOES_REALIZADAS.md)
- [Guia de Deploy](docs/DEPLOY_GUIDE.md)

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor, leia [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👥 Autores

- **Wellington de Lima Catarina** - [Lelolima](https://github.com/Lelolima)

## 🙏 Agradecimentos

- Ultralytics YOLO
- DeepSort Realtime
- FastAPI
- Comunidade AgroTech
