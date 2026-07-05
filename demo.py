"""
AgroVision AI - Demo Script
Executa demonstração do sistema com modo simulação

Usage:
    python demo.py [--simulate] [--video PATH] [--output PATH]
"""

import argparse
import sys
import time
from pathlib import Path


def print_banner():
    """Imprime banner de boas-vindas"""
    banner = r"""
    ╔═══════════════════════════════════════════════════════════╗
    ║           🐄 AgroVision AI - Demo                         ║
    ║      Sistema de Monitoramento Pecuário Inteligente        ║
    ║                                                           ║
    ║      Detecção • Rastreamento • Peso • Comportamento      ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_demo_simulation():
    """Executa demonstração em modo simulação"""
    print("\n🔄 Iniciando modo simulação...\n")

    # Importar módulos
    from agrovision.models.detector import AnimalDetector
    from agrovision.models.tracker import AnimalTracker
    from agrovision.models.weight_estimator import WeightEstimator
    from agrovision.models.behavior_classifier import BehaviorClassifier

    # Inicializar componentes
    print("📦 Carregando modelos...")
    detector = AnimalDetector(simulate=True)
    tracker = AnimalTracker()
    weight_estimator = WeightEstimator()
    behavior_classifier = BehaviorClassifier(use_heuristics=True)

    print("✅ Modelos carregados (modo simulação)")
    print()

    # Simular frames
    print("🎬 Simulando processamento de vídeo...\n")
    print(f"{'Frame':<8} {'Animais':<8} {'Track ID':<12} {'Peso':<10} {'Comportamento'}")
    print("─" * 60)

    for frame in range(1, 11):
        # Detecção simulada
        detections = detector.detect("dummy_frame")

        # Tracking
        tracked = tracker.update(detections, frame)

        # Estimar peso e comportamento para cada animal
        for animal in tracked:
            weight = weight_estimator.estimate(
                animal.bbox,
                image_height=480,
                image_width=640,
                confidence=animal.confidence
            )
            animal.weight_est = weight.weight_kg

            behavior, conf = behavior_classifier.classify(
                animal.track_id,
                frames=[],
                bboxes=[animal.bbox]
            )
            animal.behavior = behavior.value

        # Print resultados
        for animal in tracked:
            print(f"{frame:<8} {len(tracked):<8} #{animal.track_id:<10} "
                  f"{animal.weight_est:>4} kg   {animal.behavior}")

        time.sleep(0.5)

    print("─" * 60)
    print()

    # Resumo
    print("📊 Resumo da Simulação:")
    print(f"  • Frames processados: 10")
    print(f"  • Animais únicos rastreados: {tracker.get_track_count()}")
    print(f"  • Modelo detector: {detector.get_model_info()['simulate_mode'] and 'SIMULAÇÃO' or 'REAL'}")
    print()


def run_with_video(video_path: str, output_path: str = None):
    """Processa vídeo real"""
    print(f"\n🎬 Processando vídeo: {video_path}\n")

    # Tentar importar OpenCV
    try:
        import cv2
    except ImportError:
        print("❌ OpenCV não instalado. Execute: pip install opencv-python")
        return

    from agrovision.models.detector import AnimalDetector
    from agrovision.models.tracker import AnimalTracker

    # Abrir vídeo
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"❌ Não foi possível abrir o vídeo: {video_path}")
        return

    # Inicializar detector e tracker
    detector = AnimalDetector(simulate=True)  # Simulação se modelo não disponível
    tracker = AnimalTracker()

    # Info do vídeo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"📹 Vídeo: {width}x{height} @ {fps} FPS, {total_frames} frames")
    print()

    frame_count = 0
    processed = 0

    print("Processando", end="")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Processar apenas alguns frames para demo
        if frame_count % 5 != 0:
            continue

        processed += 1

        # Detectar
        detections = detector.detect(frame)
        tracked = tracker.update(detections, frame_count)

        # Draw bounding boxes
        for animal in tracked:
            x1, y1, x2, y2 = animal.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"#{animal.track_id}", (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Mostrar progresso
        if processed % 10 == 0:
            print(".", end="", flush=True)

    cap.release()
    print("\n✅ Processamento concluído!")
    print(f"   Frames processados: {processed}")
    print(f"   Animais rastreados: {tracker.get_track_count()}")


def show_api_info():
    """Mostra informações da API"""
    print("\n🌐 Informações da API:\n")
    print("Para iniciar o servidor API:")
    print("  python -m agrovision.api.app")
    print()
    print("Endpoints disponíveis:")
    print("  GET  /              - Dashboard web")
    print("  GET  /api/health    - Health check")
    print("  POST /api/upload/video - Upload de vídeo")
    print("  WS   /ws/detect     - Detecção em tempo real")
    print()


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="AgroVision AI Demo")
    parser.add_argument("--simulate", action="store_true", default=True,
                       help="Executar em modo simulação (default)")
    parser.add_argument("--video", type=str, help="Caminho do vídeo para processar")
    parser.add_argument("--output", type=str, help="Caminho do vídeo de saída")
    parser.add_argument("--api-info", action="store_true", help="Mostrar informações da API")

    args = parser.parse_args()

    if args.api_info:
        show_api_info()
        return

    if args.video:
        # Processar vídeo real
        run_with_video(args.video, args.output)
    else:
        # Rodar simulação
        run_demo_simulation()
        show_api_info()

    print("\n✨ Demo concluída!\n")
    print("Próximos passos:")
    print("  1. Acesse http://localhost:8000 para o dashboard")
    print("  2. Veja web/index.html para a interface com SVGs animados")
    print("  3. Consulte docs/CORRECOES_REALIZADAS.md para detalhes")
    print()


if __name__ == "__main__":
    main()