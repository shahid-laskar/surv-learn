"""
ai-platform/tests/test_ai_platform.py
Automated Verification Suite for SARVANETRA Modular AI Perception Platform.
Tests:
1. Versioned Event Schemas (Pydantic serialization, validation, missing fields)
2. Pure-Python ByteTracker (ID persistence, IoU association, trajectory, dwell time)
3. Spatial Rule Engine (Polygon intrusion, virtual tripwire crossing direction, loitering dwell)
4. Indian ANPR Normalization (OCR confusion correction, spaces/punctuation stripping)
5. Crowd Density & Directional People Flow Counting
6. Frigate MQTT to Kafka Normalization
7. Real ONNX Runtime Object Detection forward inference
"""

import os
import sys
import numpy as np
import pytest

from ai_platform.schemas.events import (
    BaseAiEvent,
    BoundingBox,
    ObjectDetectionPayload,
    SpatialRuleEventPayload,
    AnprEventPayload,
    CrowdDensityPayload,
    PeopleCountingPayload,
)
from ai_platform.engine.base import Detection
from ai_platform.engine.tracker import ByteTracker, calculate_iou
from ai_platform.engine.spatial_rules import SpatialRuleEngine, is_point_in_polygon, lines_intersect
from ai_platform.pipelines.anpr_pipeline import normalize_indian_plate
from ai_platform.pipelines.crowd_pipeline import CrowdAnalyticsPipeline
from ai_platform.gateway.event_gateway import AiEventGateway
from ai_platform.gateway.mqtt_adapter import FrigateMqttAdapter
from ai_platform.engine.onnx_detector import OnnxDetector


# ── 1. Event Schemas Tests ───────────────────────────────────────────────────

def test_ai_event_schema_serialization():
    payload = AnprEventPayload(
        plate="KL07 BZ 9999",
        normalized_plate="KL07BZ9999",
        confidence=0.96,
        vehicle_type="LMV",
    )
    event = BaseAiEvent(
        event_type="vehicle.anpr.detected",
        camera_id="CAM_NILAKKAL_01",
        model_name="pp-ocrv4",
        confidence=0.96,
        payload=payload.model_dump(),
    )
    data = event.model_dump()
    assert data["event_type"] == "vehicle.anpr.detected"
    assert data["event_version"] == "1.0"
    assert data["camera_id"] == "CAM_NILAKKAL_01"
    assert data["payload"]["normalized_plate"] == "KL07BZ9999"


def test_ai_event_schema_invalid_confidence():
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        BaseAiEvent(
            event_type="test",
            camera_id="CAM01",
            model_name="test",
            confidence=1.5,  # must be <= 1.0
        )


# ── 2. Spatial Tracking & IoU Tests ──────────────────────────────────────────

def test_iou_calculation():
    box1 = (0.0, 0.0, 1.0, 1.0)
    box2 = (0.0, 0.0, 1.0, 1.0)
    assert calculate_iou(box1, box2) == 1.0

    box3 = (1.0, 1.0, 2.0, 2.0)
    assert calculate_iou(box1, box3) == 0.0

    box4 = (0.5, 0.0, 1.5, 1.0)
    assert 0.3 < calculate_iou(box1, box4) < 0.4


def test_bytetrack_id_persistence_and_dwell():
    tracker = ByteTracker(iou_thresh=0.2)

    # Frame 1 at t = 100.0
    det1 = Detection("person", 0.9, 0.1, 0.1, 0.3, 0.5)
    tracked1 = tracker.update([det1], frame_timestamp=100.0)
    assert len(tracked1) == 1
    t_id = tracked1[0].track_id
    assert t_id is not None
    assert tracked1[0].attributes["dwell_time"] == 0.0

    # Frame 2 at t = 105.0 (slight movement)
    det2 = Detection("person", 0.88, 0.12, 0.11, 0.32, 0.51)
    tracked2 = tracker.update([det2], frame_timestamp=105.0)
    assert len(tracked2) == 1
    assert tracked2[0].track_id == t_id  # Track ID persisted!
    assert tracked2[0].attributes["dwell_time"] == 5.0


# ── 3. Spatial Rules Engine Tests ────────────────────────────────────────────

def test_point_in_polygon():
    polygon = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert is_point_in_polygon((0.5, 0.5), polygon) is True
    assert is_point_in_polygon((1.5, 0.5), polygon) is False


def test_line_intersection():
    p1, p2 = (0.0, 0.5), (1.0, 0.5)  # horizontal line y = 0.5
    t_prev = (0.5, 0.2)
    t_curr = (0.5, 0.8)               # vertical motion crossing y = 0.5
    assert lines_intersect(t_prev, t_curr, p1, p2) is True

    t_outside = (0.5, 0.1)
    assert lines_intersect(t_prev, t_outside, p1, p2) is False


def test_spatial_rule_engine_intrusion_and_loitering():
    engine = SpatialRuleEngine()
    engine.add_intrusion_zone("ZONE_A", [(0.0, 0.0), (0.5, 0.0), (0.5, 0.5), (0.0, 0.5)], ["person"])
    engine.add_loitering_zone("ZONE_B", [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)], min_dwell_seconds=10.0, target_classes=["person"])

    # Inside Zone A and Zone B with dwell time = 12s
    det = Detection("person", 0.95, 0.1, 0.1, 0.2, 0.2, track_id=42, attributes={"dwell_time": 12.0})
    events = engine.evaluate_detections([det])

    event_types = [e["event_type"] for e in events]
    assert "intrusion.detected" in event_types
    assert "loitering.detected" in event_types


# ── 4. ANPR Normalization Tests ──────────────────────────────────────────────

def test_indian_license_plate_normalization():
    # Spacing and dashes
    assert normalize_indian_plate("kl-01-ab-1234") == "KL01AB1234"
    assert normalize_indian_plate("TN 09 / BZ 9999") == "TN09BZ9999"

    # OCR substitutions in State Code prefix: digit '0' -> letter 'O', '1' -> 'I'
    assert normalize_indian_plate("0L01AB1234") == "OL01AB1234"
    assert normalize_indian_plate("1N09BZ1111") == "IN09BZ1111"


# ── 5. Crowd Density & Counting Tests ────────────────────────────────────────

def test_crowd_density_and_congestion_levels():
    gateway = AiEventGateway()
    pipeline = CrowdAnalyticsPipeline("CAM_CROWD_01", gateway, zone_area_sqm=100.0, high_congestion_threshold=2.0, critical_congestion_threshold=3.5)

    # 50 people in 100 sqm = 0.5/sqm -> NORMAL
    ev1 = pipeline.evaluate_crowd_count(50)
    assert ev1.payload["congestion_level"] == "NORMAL"

    # 250 people in 100 sqm = 2.5/sqm -> HIGH
    ev2 = pipeline.evaluate_crowd_count(250)
    assert ev2.payload["congestion_level"] == "HIGH"

    # 400 people in 100 sqm = 4.0/sqm -> CRITICAL
    ev3 = pipeline.evaluate_crowd_count(400)
    assert ev3.payload["congestion_level"] == "CRITICAL"


def test_people_counting_flow():
    gateway = AiEventGateway()
    pipeline = CrowdAnalyticsPipeline("CAM_GATE_01", gateway)

    ev_in = pipeline.record_people_count("IN", increment=5)
    assert ev_in.payload["current_occupancy"] == 5

    ev_out = pipeline.record_people_count("OUT", increment=2)
    assert ev_out.payload["current_occupancy"] == 3


# ── 6. Frigate MQTT Adapter Test ─────────────────────────────────────────────

def test_frigate_mqtt_normalization():
    gateway = AiEventGateway()
    adapter = FrigateMqttAdapter(gateway)

    frigate_payload = b'{"camera": "CAM_ENTRANCE", "type": "update", "after": {"label": "car", "top_score": 0.88, "box": [50, 100, 200, 300], "current_zones": []}}'
    event = adapter.normalize_and_publish("frigate/events", frigate_payload)
    assert event is not None
    assert event.event_type == "vehicle.classified"
    assert event.camera_id == "CAM_ENTRANCE"
    assert event.confidence == 0.88


# ── 7. Real ONNX Runtime Inference Test ──────────────────────────────────────

def test_real_onnx_detector_inference():
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models/yolov8n_320.onnx"))
    detector = OnnxDetector(model_path=model_path)

    # Synthetic black frame
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    dets = detector.detect(frame)
    assert isinstance(dets, list)
