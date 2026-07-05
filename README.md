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

- Feed simulado com animações SVG/CSS
- Contadores em tempo real
- Status de processamento
- Histórico de detecções

## 📊 Estrutura do Projeto

```
AgroVision-AI/
├── agrovision/
│   ├── api/
│   │   └── app.py          # API FastAPI
│   ├── models/
│   │   ├── detector.py     # Detecção YOLO
│   │   ├── tracker.py      # Tracking DeepSort
│   │   ├── weight_est.py   # Estimativa de peso
│   │   └── behavior.py     # Classificador de comportamento
│   ├── utils/
│   │   ├── video.py        # Processamento de vídeo
│   │   ├── database.py     # Banco de dados
│   │   └── logger.py       # Logging estruturado
│   └── config/
│       └── settings.py     # Configurações
├── web/
│   ├── index.html          # Dashboard web
│   ├── css/
│   │   └── styles.css      # Estilos e animações
│   ├── js/
│   │   └── dashboard.js    # Lógica do dashboard
│   └── svg/
│       └── animations.svg  # SVGs animados
├── scripts/
│   ├── download_models.py  # Download de modelos
│   └── setup.sh            # Setup completo
├── docker/
│   └── Dockerfile          # Configuração Docker
├── tests/
│   └── test_api.py         # Testes unitários
├── requirements.txt
├── docker-compose.yml
└── README.md
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