"""
AgroVision AI - Pacote principal
"""

__version__ = "2.0.0"
__author__ = "Leonardo Lima"
__email__ = "contato@agrovision.ai"

_LAZY = {
    "app": "agrovision.api.app",
    "AnimalDetector": "agrovision.models.detector",
    "AnimalTracker": "agrovision.models.tracker",
    "WeightEstimator": "agrovision.models.weight_estimator",
    "BehaviorClassifier": "agrovision.models.behavior_classifier",
}


def __getattr__(name):
    """Importação preguiçosa (evita carregar torch/FastAPI ao importar o pacote)."""
    if name in _LAZY:
        import importlib

        return getattr(importlib.import_module(_LAZY[name]), name)
    raise AttributeError(name)


__all__ = [
    "app",
    "AnimalDetector",
    "AnimalTracker",
    "WeightEstimator",
    "BehaviorClassifier",
]