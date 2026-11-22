# Auditoria técnica — 2026-11-22

Ambiente: Windows 11, Python 3.11 (uv), torch CPU. Sem GPU, sem câmera, sem pesos YOLO/LightGBM.

## Estado anterior

| Item | Resultado |
|------|-----------|
| Finalidade | Monitoramento pecuário: detecção (YOLO/ultralytics), tracking (IoU próprio), estimativa de peso (fórmula/LightGBM), comportamento (heurística), API FastAPI + dashboard estático |
| Instalação | **Falhava**: `pip install -r requirements.txt` → `sort>=0.3.1` não existe no PyPI |
| Inicialização | **Falhava**: `agrovision/api/app.py` importava `analysis_router`/`results_router`, inexistentes em `routes.py` |
| Testes | `pytest` → 4 failed, 3 errors (todos por esse ImportError) |
| CI | Nenhum workflow |
| Vulnerabilidades | Não auditável antes (resolução falhava). Depois: `pip-audit -r requirements.txt` → *No known vulnerabilities found* |
| Segredos | Nenhum (busca por padrões em todo o histórico; `.env.example` só com placeholders comentados). gitleaks indisponível na máquina |
| .gitignore | Inexistente |

## Problemas e correções

| # | Sev. | Problema | Evidência | Correção |
|---|------|----------|-----------|----------|
| 1 | P0 | Dependência inexistente `sort` | erro do resolvedor | removida; `requirements.txt` só com o que o código importa; `requirements-dev.txt`, `requirements-optional.txt` |
| 2 | P0 | API não iniciava (ImportError) | testes; `test_routes_exports_routers` | routers exportados; `/api/analyze/image` e `/video` implementados com o pipeline real (antes stubs fixos) |
| 3 | P1 | **Dados simulados passando por reais**: sem pesos, o detector gera detecções aleatórias (confiança 0.85–0.99) e o upload as devolvia sem aviso | `test_image_endpoint_flags_simulated_results`, `test_health_reports_simulation_mode` | campos `simulated` / `simulation_mode` / `status: simulated` em todas as saídas. O modo simulação foi mantido (é funcionalidade existente) |
| 4 | P1 | YOLO COCO: classe 0 (`person`) rotulada como "vaca" (mapa fixo 0..5) | `test_class_name_uses_model_names` | usa `result.names` do modelo, traduz cow/horse/sheep/pig |
| 5 | P1 | Bbox simulada com `x2 < x1` (largura negativa no estimador de peso) | `test_simulated_bbox_is_xyxy` | gera `[x1, y1, x2, y2]` válido |
| 6 | P1 | Estimador de peso e classificador nunca carregados na API → upload nunca estimava peso/comportamento | leitura de `load_models` | carregados no lifespan |
| 7 | P1 | WebSocket com detector real passava string ao YOLO e tentava serializar dataclasses (quebra) | `test_websocket_rejects_invalid_frame_when_detector_real` | decodifica base64 JPEG/PNG; `jsonable_encoder` |
| 8 | P2 | Raça `angus` caía no coeficiente default (chave `"angu s"`) | `test_angus_breed_coefficients_used` | chave corrigida |
| 9 | P2 | CORS `*` com `allow_credentials=True` | código | credenciais só com origens explícitas |
| 10 | P2 | Resposta de upload expunha caminho temporário do servidor; erro de vídeo virava 200 com `error` | `test_video_upload_corrupt_returns_422` | campo `filename`; vídeo ilegível → 422; erro 500 sem detalhes internos |
| 11 | P2 | `MAX_VIDEO_SIZE_MB`/`FRAME_SKIP` ignorados; console script `agrovision=...:main` apontava para função inexistente | código | usa settings; `main()` adicionada |
| 12 | P2 | Sem CI, sem .gitignore | — | workflow (ruff, compileall + `pip install -e .`, pytest), `contents: read`, actions por SHA; `.gitignore` |
| 13 | P2 | README prometia `/api/results/{job_id}` e `docker-compose.test.yml` inexistentes | leitura | README corrigido, seção "Modo simulação" |

Mudança de contrato: a resposta de `/api/upload/video` troca `video_path` (caminho temporário já apagado) por `filename` e ganha `simulated`.

## Testes executados (resultados reais)

```
antes:  python -m pytest -q          -> 4 failed, 3 errors
depois: python -m pytest -q -p no:cacheprovider -> 17 passed
        ruff check --select E9,F63,F7,F82 .      -> All checks passed!
        pip-audit -r requirements.txt            -> No known vulnerabilities found
        uvicorn agrovision.api.app:app; GET /api/health -> 200 (simulation_mode: true); GET / -> 200
        pip install --no-deps -e . ; from agrovision.api.app import main -> ok
```

## Não executado / riscos residuais

- Detecção real com YOLO: não validada (não baixei pesos; o caminho padrão `yolov5s.pt` é relativo ao diretório de execução).
- Estimativa de peso é uma fórmula empírica sem calibração; não há modelo LightGBM no repositório.
- Docker/nginx não construídos. Dashboard `web/` é estático (dados do JS não verificados).
- `DEBUG=True` é o padrão em `settings.py` (mantido; `.env.example` agora usa `False`).
- `requirements.txt` usa limites inferiores (`>=`), não pins: builds futuros podem variar.
