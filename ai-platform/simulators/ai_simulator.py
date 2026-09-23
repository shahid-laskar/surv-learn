#!/usr/bin/env python3
"""
ai-platform/simulators/ai_simulator.py
Full-Spectrum Synthetic AI Perception & Event Simulator.
Implements Section 61: Generates standardized events across all 15 perception classes:
  1. Object Detection (Person, Car, Motorcycle, Bus, Truck)
  2. Spatial Intrusion & Virtual Tripwire Line Crossing
  3. Stationary Loitering & Dwell Alarms
  4. ANPR License Plate Ingest with Hotlist/Watchlist Alarms
  5. Crowd Density Estimation & Congestion Alarms
  6. Bidirectional Pedestrian Flow & Occupancy Counting
  7. Human Pose Collapse & Fall Detection
  8. Missing Person / Biometric Face Search Candidates
Uses exact canonical BaseAiEvent contracts to feed Kafka and the central VMS platform.
"""

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ai_platform.schemas.events import (
    BaseAiEvent,
    BoundingBox,
    ObjectDetectionPayload,
    SpatialRuleEventPayload,
    AnprEventPayload,
    PeopleCountingPayload,
    CrowdDensityPayload,
    FallDetectionPayload,
    FaceMatchPayload,
)
from ai_platform.gateway.event_gateway import AiEventGateway
from ai_platform.pipelines.anpr_pipeline import normalize_indian_plate

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ai-sim] %(message)s")
log = logging.getLogger("ai_simulator")

# Realistic Kerala / Sabarimala testing locations
CAMERAS = ["CAMKRTVM0001", "CAM_NILAKKAL_GATE1", "CAM_NILAKKAL_GATE2", "CAM_PAMPA_TREK01", "CAM_SANNIDHANAM_MAIN"]
ZONES = ["ZONE_PILGRIM_QUEUE", "ZONE_VIP_ENTRY", "ZONE_PARKING_GROUND1", "ZONE_SECURITY_PERIMETER"]
WATCHLIST_PLATES = [
    ("KL07BH9999", "WANTED", "Robbery suspect vehicle (Pathanamthitta)"),
    ("KL01DZ0007", "STOLEN", "Stolen Fortuner from Thiruvananthapuram"),
    ("KL03P1111",  "SUSPICIOUS", "Unauthorized night access vehicle"),
]


class AiSimulator:
    def __init__(self, gateway: Optional[AiEventGateway] = None):
        self.gateway = gateway or AiEventGateway()
        self.people_count_in = 0
        self.people_count_out = 0

    def generate_detection_event(self, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        cls_name = random.choice(["person", "car", "motorcycle", "bus", "truck"])
        score = round(random.uniform(0.75, 0.98), 2)
        box = BoundingBox(
            x1=round(random.uniform(0.1, 0.4), 3),
            y1=round(random.uniform(0.2, 0.5), 3),
            x2=round(random.uniform(0.5, 0.8), 3),
            y2=round(random.uniform(0.6, 0.9), 3),
        )
        payload = ObjectDetectionPayload(
            track_id=random.randint(101, 999),
            class_name=cls_name,
            confidence=score,
            bbox=box,
        )
        event = BaseAiEvent(
            event_type="person.detected" if cls_name == "person" else "vehicle.classified",
            camera_id=cam,
            model_name="yolox-coco-detector",
            model_version="0.3",
            confidence=score,
            source="ai-simulator",
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_spatial_rule_event(self, rule_type: str = "intrusion", camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        zone = random.choice(ZONES)
        track_id = random.randint(201, 499)
        obj_class = random.choice(["person", "motorcycle", "car"])
        dwell = round(random.uniform(12.0, 45.0), 1) if rule_type == "loitering" else None
        direction = random.choice(["A_TO_B", "B_TO_A"]) if rule_type == "line_crossing" else None

        payload = SpatialRuleEventPayload(
            rule_type=rule_type,
            zone_id=zone,
            track_id=track_id,
            object_class=obj_class,
            confidence=0.94,
            dwell_time_seconds=dwell,
            direction=direction,
        )
        event = BaseAiEvent(
            event_type=f"{rule_type}.detected",
            camera_id=cam,
            model_name="spatial-rule-engine",
            model_version="1.0",
            confidence=0.94,
            source="ai-simulator",
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_anpr_event(self, force_watchlist: bool = False, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        if force_watchlist:
            plate_tuple = random.choice(WATCHLIST_PLATES)
            raw_plate = plate_tuple[0]
            conf = 0.98
        else:
            rto = random.choice(["KL01", "KL07", "KL03", "TN09", "KA04"])
            series = random.choice(["AZ", "BZ", "CB", "M", "P"])
            num = f"{random.randint(1000, 9999)}"
            raw_plate = f"{rto} {series} {num}"
            conf = round(random.uniform(0.85, 0.99), 2)

        normalized = normalize_indian_plate(raw_plate)
        payload = AnprEventPayload(
            plate=raw_plate,
            normalized_plate=normalized,
            confidence=conf,
            vehicle_type=random.choice(["CAR", "LMV", "BUS"]),
            vehicle_color=random.choice(["white", "silver", "black", "red"]),
            snapshot_key=f"anpr/{cam}/{normalized}_{int(time.time())}.jpg",
        )
        event = BaseAiEvent(
            event_type="vehicle.anpr.detected",
            camera_id=cam,
            model_name="pp-ocrv4-plate-engine",
            model_version="4.0",
            confidence=conf,
            source="ai-simulator",
            evidence_references={"snapshot_key": payload.snapshot_key},
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_crowd_event(self, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        count = random.randint(40, 350)
        density = round(count / 100.0, 2)  # assuming 100 sqm zone
        level = "CRITICAL" if density >= 3.0 else "HIGH" if density >= 2.0 else "MODERATE"

        payload = CrowdDensityPayload(
            zone_id="ZONE_PILGRIM_SANNIDHANAM",
            estimated_count=count,
            persons_per_square_meter=density,
            congestion_level=level,
        )
        event = BaseAiEvent(
            event_type="crowd.density.updated",
            camera_id=cam,
            model_name="crowd-density-regressor",
            model_version="1.0",
            confidence=0.91,
            source="ai-simulator",
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_people_count_event(self, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        direction = random.choice(["IN", "OUT"])
        inc = random.randint(1, 3)
        if direction == "IN":
            self.people_count_in += inc
        else:
            self.people_count_out += inc

        occ = max(0, self.people_count_in - self.people_count_out)
        payload = PeopleCountingPayload(
            gate_id="GATE_PAMPA_NORTH",
            direction=direction,
            count_increment=inc,
            total_in=self.people_count_in,
            total_out=self.people_count_out,
            current_occupancy=occ,
        )
        event = BaseAiEvent(
            event_type="person.counted",
            camera_id=cam,
            model_name="tripwire-people-counter",
            model_version="1.0",
            confidence=0.96,
            source="ai-simulator",
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_fall_event(self, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        payload = FallDetectionPayload(
            track_id=random.randint(501, 700),
            confidence=0.92,
            body_orientation="HORIZONTAL",
            duration_on_ground_seconds=round(random.uniform(4.0, 15.0), 1),
            bbox=BoundingBox(x1=0.2, y1=0.7, x2=0.5, y2=0.9),
        )
        event = BaseAiEvent(
            event_type="fall.detected",
            camera_id=cam,
            model_name="mediapipe-pose-engine",
            model_version="0.10",
            confidence=0.92,
            source="ai-simulator",
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event

    def generate_face_match_event(self, camera_id: Optional[str] = None) -> BaseAiEvent:
        cam = camera_id or random.choice(CAMERAS)
        payload = FaceMatchPayload(
            candidate_id="MISSING-2026-084",
            person_name="Pilgrim Visitor (Reported Missing)",
            category="MISSING_PERSON",
            match_similarity=round(random.uniform(0.88, 0.96), 2),
            gallery_id="POLICE_HQ_MISSING_DATABASE",
            last_seen_camera_id=cam,
            face_snapshot_key=f"face/{cam}/match_{int(time.time())}.jpg",
        )
        event = BaseAiEvent(
            event_type="face.match.detected",
            camera_id=cam,
            model_name="mobilefacenet-open-weights",
            model_version="1.0",
            confidence=payload.match_similarity,
            source="ai-simulator",
            evidence_references={"face_snapshot_key": payload.face_snapshot_key},
            payload=payload.model_dump(),
        )
        self.gateway.publish_event(event)
        return event


def main():
    parser = argparse.ArgumentParser(description="SARVANETRA Synthetic AI Perception Simulator")
    parser.add_argument("--count", type=int, default=10, help="Number of events to generate")
    parser.add_argument("--interval", type=float, default=0.2, help="Seconds between events")
    parser.add_argument("--type", default="all", choices=["all", "detection", "spatial", "anpr", "crowd", "counting", "fall", "face"])
    args = parser.parse_args()

    sim = AiSimulator()
    log.info(f"Running AI simulator: {args.count} events, type={args.type}, interval={args.interval}s")

    for i in range(args.count):
        ev_type = args.type
        if ev_type == "all":
            ev_type = random.choice(["detection", "spatial", "anpr", "crowd", "counting", "fall", "face"])

        if ev_type == "detection":
            ev = sim.generate_detection_event()
        elif ev_type == "spatial":
            stype = random.choice(["intrusion", "line_crossing", "loitering"])
            ev = sim.generate_spatial_rule_event(rule_type=stype)
        elif ev_type == "anpr":
            wl = random.random() < 0.25
            ev = sim.generate_anpr_event(force_watchlist=wl)
        elif ev_type == "crowd":
            ev = sim.generate_crowd_event()
        elif ev_type == "counting":
            ev = sim.generate_people_count_event()
        elif ev_type == "fall":
            ev = sim.generate_fall_event()
        elif ev_type == "face":
            ev = sim.generate_face_match_event()

        log.info(f"[{i+1}/{args.count}] Generated {ev.event_type} for camera {ev.camera_id} (conf={ev.confidence})")
        time.sleep(args.interval)

    log.info("Simulation completed successfully.")


if __name__ == "__main__":
    main()
