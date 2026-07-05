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

- Python 3.9+
- NVIDIA GPU (opcional, para inferência acelerada)
- Docker e Docker Compose (para deploy containerizado)

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/Lelolima/AgroVision-AI.git
cd AgroVision-AI
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Baixe os modelos pré-treinados

Execute o script de setup para baixar automaticamente os modelos:

```bash
python scripts/download_models.py
```

Ou execute manualmente:

```bash
python -c "from ultralytics import YOLO; YOLO('yolov5s.pt')"
```

### 4. Inicie o servidor

```bash
# Modo desenvolvimento
python -m agrovision.api.app

# Modo produção com Docker
docker-compose up
```

## 🌐 API Endpoints

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/` | GET | Dashboard web com SVGs animados |
| `/api/health` | GET | Health check |
| `/api/upload/video` | POST | Upload de vídeo para análise |
| `/api/analyze/stream` | POST | Análise de stream em tempo real |
| `/api/results/{job_id}` | GET | Resultados de análise |
| `/ws/detect` | WebSocket | Detecção em tempo real |

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
# Testes unitários
pytest tests/ -v

# Teste de integração com Docker
docker-compose -f docker-compose.test.yml up
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

- **Leonardo Lima** - [Lelolima](https://github.com/Lelolima)

## 🙏 Agradecimentos

- Ultralytics YOLO
- DeepSort Realtime
- FastAPI
- Comunidade AgroTech