"""
ai-platform/pipelines/object_pipeline.py
End-to-End Vision Analytics Pipeline.
Connects Detector -> Tracker -> Spatial Rule Engine -> Event Gateway.
Processes frames, maintains tracks, detects intrusions/tripwires/loitering, and publishes events.
"""

from typing import List, Dict, Any, Optional
import time
from ai_platform.engine.base import BaseDetector, Detection
from ai_platform.engine.tracker import ByteTracker
from ai_platform.engine.spatial_rules import SpatialRuleEngine
from ai_platform.schemas.events import BaseAiEvent
from ai_platform.gateway.event_gateway import AiEventGateway


class ObjectAnalyticsPipeline:
    def __init__(
        self,
        camera_id: str,
        detector: BaseDetector,
        gateway: AiEventGateway,
        tracker: Optional[ByteTracker] = None,
        rule_engine: Optional[SpatialRuleEngine] = None,
    ):
        self.camera_id = camera_id
        self.detector = detector
        self.gateway = gateway
        self.tracker = tracker or ByteTracker()
        self.rule_engine = rule_engine or SpatialRuleEngine()

    def process_frame(self, frame: Any, timestamp: Optional[float] = None) -> List[BaseAiEvent]:
        """Runs detection, tracking, and spatial rule evaluation on a video frame."""
        if timestamp is None:
            timestamp = time.time()

        # 1. Forward pass detection
        raw_detections = self.detector.detect(frame)

        # 2. Association & Tracking
        tracked_detections = self.tracker.update(raw_detections, timestamp)

        # 3. Evaluate Spatial Rules
        rule_events = self.rule_engine.evaluate_detections(tracked_detections, self.tracker.tracks)

        # 4. Standardize and Dispatch Events
        published_events = []
        for rev in rule_events:
            event = BaseAiEvent(
                event_type=rev["event_type"],
                camera_id=self.camera_id,
                model_name=self.detector.model_name,
                model_version="1.0",
                confidence=rev.get("confidence", 0.9),
                source="ai-object-pipeline",
                payload=rev,
            )
            self.gateway.publish_event(event)
            published_events.append(event)

        return published_events
