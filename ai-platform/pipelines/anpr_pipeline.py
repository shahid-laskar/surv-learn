"""
ai-platform/pipelines/anpr_pipeline.py
Dedicated ANPR (Automatic Number Plate Recognition) Pipeline.
Implements Sections 22, 23, 25 of the Master Mission.
Handles plate detection, OCR recognition, Indian license plate normalization,
and publication to the central `vehicle.anpr.detected` Kafka topic.
"""

import re
from typing import Dict, Any, Optional, Tuple
from ai_platform.engine.base import BaseOcrEngine
from ai_platform.schemas.events import BaseAiEvent, AnprEventPayload
from ai_platform.gateway.event_gateway import AiEventGateway


def normalize_indian_plate(raw_text: str) -> str:
    """
    Normalizes Indian vehicle license plate text:
    1. Converts to uppercase.
    2. Strips whitespace, hyphens, periods, and special characters.
    3. Handles standard OCR substitution rules for state code (letters) and number series (digits).
    """
    clean = re.sub(r"[^A-Za-z0-9]", "", raw_text.upper())
    if len(clean) < 4:
        return clean

    # First two characters are State Code (e.g. KL, TN, KA) -> must be letters
    state_code = list(clean[:2])
    digit_to_letter = {"0": "O", "1": "I", "8": "B", "5": "S", "2": "Z"}
    for i in range(2):
        if state_code[i] in digit_to_letter:
            state_code[i] = digit_to_letter[state_code[i]]

    # Remaining suffix
    suffix = clean[2:]
    return "".join(state_code) + suffix


class AnprPipeline:
    def __init__(self, camera_id: str, ocr_engine: BaseOcrEngine, gateway: AiEventGateway, site_id: int = 1):
        self.camera_id = camera_id
        self.ocr_engine = ocr_engine
        self.gateway = gateway
        self.site_id = site_id

    def process_plate_crop(
        self,
        plate_crop: Any,
        vehicle_type: str = "CAR",
        vehicle_color: Optional[str] = None,
        snapshot_key: Optional[str] = None,
    ) -> BaseAiEvent:
        """Processes a cropped plate image and produces a normalized ANPR event."""
        raw_plate, confidence = self.ocr_engine.recognize_plate(plate_crop)
        normalized = normalize_indian_plate(raw_plate)

        payload = AnprEventPayload(
            plate=raw_plate,
            normalized_plate=normalized,
            confidence=confidence,
            vehicle_type=vehicle_type,
            vehicle_color=vehicle_color,
            snapshot_key=snapshot_key,
        )

        event = BaseAiEvent(
            event_type="vehicle.anpr.detected",
            camera_id=self.camera_id,
            site_id=self.site_id,
            model_name="pp-ocrv4-plate-engine",
            model_version="4.0",
            confidence=confidence,
            source="ai-anpr-pipeline",
            evidence_references={"snapshot_key": snapshot_key} if snapshot_key else {},
            payload=payload.model_dump(),
        )

        self.gateway.publish_event(event)
        return event
