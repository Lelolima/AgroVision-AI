"""
Script para download dos modelos pré-treinados
Executar: python scripts/download_models.py
"""

import os
import sys
from pathlib import Path

def download_yolo_model():
    """Baixa modelo YOLOv5s"""
    print("📥 Baixando modelo YOLOv5s...")

    try:
        from ultralytics import YOLO

        # Download do modelo
        model = YOLO('yolov5s.pt')
        print("✅ Modelo YOLOv5s baixado com sucesso!")
        return True

    except ImportError:
        print("❌ Ultralytics não instalado. Execute: pip install ultralytics")
        return False
    except Exception as e:
        print(f"❌ Erro ao baixar modelo: {e}")
        return False


def create_placeholder_models():
    """Cria modelos placeholder para testes"""
    model_dir = Path(__file__).parent.parent / "agrovision" / "models" / "weights"
    model_dir.mkdir(parents=True, exist_ok=True)

    # Criar arquivo de indicador
    indicator_file = model_dir / ".gitkeep"
    indicator_file.write_text("# Model weights directory\n")

    print(f"✅ Diretório de modelos criado: {model_dir}")

    # Criar arquivo de instrução
    readme = model_dir / "README.md"
    readme.write_text("""# Model Weights

Este diretório contém os modelos pré-treinados.

## Download

Execute o script de setup para baixar automaticamente:

```bash
python scripts/download_models.py
```

## Modelos necessários

- `yolov5s.pt` - Detector YOLOv5 small
- `weight_model.pkl` - Estimador de peso (LightGBM)
- `behavior_model.pth` - Classificador de comportamento (CNN 3D)

## Links

- YOLOv5: https://github.com/ultralytics/yolov5
- LightGBM: https://github.com/microsoft/LightGBM
""")

    print("✅ README de modelos criado")


def main():
    print("=" * 50)
    print("AgroVision AI - Setup de Modelos")
    print("=" * 50)
    print()

    # Criar estrutura de diretórios
    create_placeholder_models()
    print()

    # Tentar download do modelo YOLO
    success = download_yolo_model()

    print()
    print("=" * 50)
    if success:
        print("✅ Setup concluído com sucesso!")
        print()
        print("Próximos passos:")
        print("1. Execute: python -m agrovision.api.app")
        print("2. Acesse: http://localhost:8000")
    else:
        print("⚠️ Setup parcial concluído.")
        print()
        print("O modo simulação estará disponível.")
        print("Para modelos reais, instale: pip install ultralytics")

    print("=" * 50)


if __name__ == "__main__":
    main()