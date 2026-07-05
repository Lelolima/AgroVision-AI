"""
AgroVision AI - Pacote principal
"""

__version__ = "2.0.0"
__author__ = "Leonardo Lima"
__email__ = "contato@agrovision.ai"

from agrovision.api.app import app
from agrovision.models.detector import AnimalDetector
from agrovision.models.tracker import AnimalTracker
from agrovision.models.weight_estimator import WeightEstimator
from agrovision.models.behavior_classifier import BehaviorClassifier

__all__ = [
    "app",
    "AnimalDetector",
    "AnimalTracker",
    "WeightEstimator",
    "BehaviorClassifier",
]