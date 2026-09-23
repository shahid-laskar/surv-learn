"""
ai-platform/gateway/mqtt_adapter.py
Frigate / Edge MQTT to Apache Kafka Normalization Adapter.
Implements Section 41: Bridges edge MQTT detection streams into SARVANETRA's canonical Kafka topics.
"""

import json
import logging
from typing import Dict, Any, Optional
from ai_platform.schemas.events import BaseAiEvent, BoundingBox
from ai_platform.gateway.event_gateway import AiEventGateway

log = logging.getLogger("mqtt_adapter")


class FrigateMqttAdapter:
    """Normalizes Frigate NVR MQTT payloads into SARVANETRA BaseAiEvent records."""

    def __init__(self, gateway: AiEventGateway):
        self.gateway = gateway

    def normalize_and_publish(self, topic: str, payload_bytes: bytes) -> Optional[BaseAiEvent]:
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            log.warning(f"Malformed MQTT JSON payload on topic {topic}: {e}")
            return None

        # Frigate topic format: frigate/events or frigate/<camera_name>/<event>
        camera_name = payload.get("camera", "unknown_camera")
        event_type = payload.get("type", "update")
        after_obj = payload.get("after", {})

        if not after_obj:
            return None

        label = after_obj.get("label", "object")
        score = float(after_obj.get("top_score", 0.8))
        box = after_obj.get("box", [0, 0, 0, 0])
        entered_zones = after_obj.get("current_zones", [])

        # Map to canonical SARVANETRA event
        if entered_zones:
            mapped_type = "intrusion.detected"
        elif label == "person":
            mapped_type = "person.detected"
        elif label in ("car", "motorcycle", "bus", "truck"):
            mapped_type = "vehicle.classified"
        else:
            mapped_type = "object.detected"

        event = BaseAiEvent(
            event_type=mapped_type,
            camera_id=camera_name,
            model_name="frigate-edge-detector",
            model_version="0.14",
            confidence=score,
            source="frigate-mqtt",
            evidence_references={
                "frigate_event_id": payload.get("id"),
                "snapshot_url": f"http://frigate:5000/api/events/{payload.get('id')}/snapshot.jpg"
            },
            payload={
                "class_name": label,
                "zones": entered_zones,
                "bbox": {"x1": box[0], "y1": box[1], "x2": box[2], "y2": box[3]},
            }
        )

        self.gateway.publish_event(event)
        return event
