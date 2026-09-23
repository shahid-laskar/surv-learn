"""
ai-platform/pipelines/crowd_pipeline.py
Crowd Density & People Counting Analytics Pipeline.
Implements Sections 29, 31, 33 of the Master Mission.
Tracks continuous zone density (persons/m²), triggers congestion threshold alarms,
and monitors directional line-crossing pedestrian flow.
"""

from typing import Dict, Any, Optional, List, Tuple
from ai_platform.engine.base import BaseCrowdEstimator
from ai_platform.schemas.events import BaseAiEvent, CrowdDensityPayload, PeopleCountingPayload
from ai_platform.gateway.event_gateway import AiEventGateway


class CrowdAnalyticsPipeline:
    def __init__(
        self,
        camera_id: str,
        gateway: AiEventGateway,
        zone_area_sqm: float = 100.0,
        high_congestion_threshold: float = 2.5,
        critical_congestion_threshold: float = 4.0,
        site_id: int = 1,
    ):
        self.camera_id = camera_id
        self.gateway = gateway
        self.zone_area_sqm = max(1.0, zone_area_sqm)
        self.high_thresh = high_congestion_threshold
        self.crit_thresh = critical_congestion_threshold
        self.site_id = site_id

        self.total_in = 0
        self.total_out = 0

    def evaluate_crowd_count(self, detected_people_count: int, zone_id: str = "ZONE_MAIN") -> BaseAiEvent:
        """Computes density and evaluates congestion level."""
        density = detected_people_count / self.zone_area_sqm

        if density >= self.crit_thresh:
            level = "CRITICAL"
        elif density >= self.high_thresh:
            level = "HIGH"
        elif density >= 1.0:
            level = "MODERATE"
        else:
            level = "NORMAL"

        payload = CrowdDensityPayload(
            zone_id=zone_id,
            estimated_count=detected_people_count,
            persons_per_square_meter=round(density, 2),
            congestion_level=level,
        )

        event = BaseAiEvent(
            event_type="crowd.density.updated",
            camera_id=self.camera_id,
            site_id=self.site_id,
            model_name="crowd-density-regressor",
            model_version="1.0",
            confidence=0.92,
            source="ai-crowd-pipeline",
            payload=payload.model_dump(),
        )

        self.gateway.publish_event(event)
        return event

    def record_people_count(self, direction: str, increment: int = 1, gate_id: str = "GATE_ENTRY") -> BaseAiEvent:
        """Records directional pedestrian counting."""
        if direction.upper() in ("IN", "ENTRY"):
            self.total_in += increment
        elif direction.upper() in ("OUT", "EXIT"):
            self.total_out += increment

        current_occupancy = max(0, self.total_in - self.total_out)

        payload = PeopleCountingPayload(
            gate_id=gate_id,
            direction=direction.upper(),
            count_increment=increment,
            total_in=self.total_in,
            total_out=self.total_out,
            current_occupancy=current_occupancy,
        )

        event = BaseAiEvent(
            event_type="person.counted",
            camera_id=self.camera_id,
            site_id=self.site_id,
            model_name="tripwire-people-counter",
            model_version="1.0",
            confidence=0.95,
            source="ai-crowd-pipeline",
            payload=payload.model_dump(),
        )

        self.gateway.publish_event(event)
        return event
