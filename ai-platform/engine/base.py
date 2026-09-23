"""
ai-platform/engine/base.py
Abstract Base Classes and Interfaces for Replaceable AI Inference Modules.
Ensures zero coupling between SARVANETRA core and specific AI frameworks.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import time


@dataclass
class Detection:
    class_name: str
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    track_id: Optional[int] = None
    attributes: Dict[str, Any] = field(default_factory=dict)

    @property
    def bbox(self) -> Tuple[float, float, float, float]:
        return (self.x1, self.y1, self.x2, self.y2)

    @property
    def centroid(self) -> Tuple[float, float]:
        return ((self.x1 + self.x2) / 2.0, (self.y1 + self.y2) / 2.0)


class BaseDetector(ABC):
    """Abstract object detection engine (e.g., YOLOX, RT-DETR, NanoDet)."""

    def __init__(self, model_name: str, model_path: Optional[str] = None, confidence_threshold: float = 0.5):
        self.model_name = model_name
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold

    @abstractmethod
    def detect(self, frame: Any) -> List[Detection]:
        """Performs forward pass detection on a single frame."""
        pass


class BaseTracker(ABC):
    """Abstract multi-object tracker (e.g., ByteTrack, CentroidTracker)."""

    @abstractmethod
    def update(self, detections: List[Detection], frame_timestamp: float) -> List[Detection]:
        """Associates detections across consecutive frames and assigns persistent track IDs."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Clears active tracks (e.g., upon stream reconnect)."""
        pass


class BaseOcrEngine(ABC):
    """Abstract Optical Character Recognition engine for vehicle plates (e.g., PP-OCRv4)."""

    @abstractmethod
    def recognize_plate(self, plate_crop: Any) -> Tuple[str, float]:
        """Returns (raw_text, confidence)."""
        pass


class BaseCrowdEstimator(ABC):
    """Abstract crowd density regression and head-counting engine."""

    @abstractmethod
    def estimate_density(self, frame: Any, zone_polygon: Optional[List[Tuple[float, float]]] = None) -> Dict[str, Any]:
        """Returns dict containing estimated_count, density_per_sqm, and congestion_level."""
        pass


class BaseForecaster(ABC):
    """Abstract predictive time-series forecaster (e.g., Prophet, ARIMA, Exponential Smoothing)."""

    @abstractmethod
    def predict(self, historical_series: List[float], horizon_steps: int = 12) -> List[float]:
        """Returns predicted future values for the given forecast horizon."""
        pass
