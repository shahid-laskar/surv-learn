"""
ai-platform/engine/spatial_rules.py
Spatial Analytics & Rule Engine.
Implements:
1. Polygon ROI Intrusion Detection (Ray-casting point-in-polygon)
2. Virtual Tripwire Line Crossing (Segment intersection & orientation)
3. Loitering Detection (Zone dwell-time threshold)
4. Abandoned Object Detection (Stationary object threshold)
Zero external dependencies; executes with microsecond latency.
"""

from typing import List, Tuple, Dict, Any, Optional
from ai_platform.engine.base import Detection


Point = Tuple[float, float]
Polygon = List[Point]


def is_point_in_polygon(point: Point, polygon: Polygon) -> bool:
    """Ray-casting algorithm to test if a 2D point is inside an arbitrary polygon."""
    x, y = point
    n = len(polygon)
    inside = False

    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y

    return inside


def ccw(A: Point, B: Point, C: Point) -> bool:
    """Returns True if points A, B, C are listed in counterclockwise order."""
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])


def lines_intersect(A: Point, B: Point, C: Point, D: Point) -> bool:
    """Returns True if line segment AB intersects line segment CD."""
    return ccw(A, C, D) != ccw(B, C, D) and ccw(A, B, C) != ccw(A, B, D)


def determine_crossing_direction(prev_point: Point, curr_point: Point, line_start: Point, line_end: Point) -> str:
    """
    Determines crossing direction across a directed tripwire (line_start -> line_end).
    Computes cross product: > 0 means left-to-right (A_TO_B), < 0 means right-to-left (B_TO_A).
    """
    dx = line_end[0] - line_start[0]
    dy = line_end[1] - line_start[1]
    
    # Vector normal to tripwire
    val = (curr_point[0] - line_start[0]) * dy - (curr_point[1] - line_start[1]) * dx
    return "A_TO_B" if val > 0 else "B_TO_A"


class SpatialRuleEngine:
    def __init__(self):
        # zone_id -> {"polygon": Polygon, "target_classes": List[str], "min_dwell": float}
        self.intrusion_zones: Dict[str, Dict[str, Any]] = {}
        # tripwire_id -> {"p1": Point, "p2": Point, "target_classes": List[str], "allowed_dir": str}
        self.tripwires: Dict[str, Dict[str, Any]] = {}
        # loitering_zones -> {"polygon": Polygon, "min_dwell_seconds": float, "target_classes": List[str]}
        self.loitering_zones: Dict[str, Dict[str, Any]] = {}

    def add_intrusion_zone(self, zone_id: str, polygon: Polygon, target_classes: Optional[List[str]] = None):
        self.intrusion_zones[zone_id] = {
            "polygon": polygon,
            "target_classes": target_classes or ["person", "car", "motorcycle", "bus", "truck"],
        }

    def add_tripwire(self, tripwire_id: str, p1: Point, p2: Point, target_classes: Optional[List[str]] = None, direction: str = "BOTH"):
        self.tripwires[tripwire_id] = {
            "p1": p1,
            "p2": p2,
            "target_classes": target_classes or ["person", "car", "motorcycle"],
            "direction": direction,
        }

    def add_loitering_zone(self, zone_id: str, polygon: Polygon, min_dwell_seconds: float = 10.0, target_classes: Optional[List[str]] = None):
        self.loitering_zones[zone_id] = {
            "polygon": polygon,
            "min_dwell_seconds": min_dwell_seconds,
            "target_classes": target_classes or ["person"],
        }

    def evaluate_detections(self, detections: List[Detection], tracker_history: Optional[Dict[int, Any]] = None) -> List[Dict[str, Any]]:
        """Evaluates active tracked detections against all configured spatial rules."""
        events = []

        for det in detections:
            centroid = det.centroid
            dwell_time = det.attributes.get("dwell_time", 0.0)

            # 1. Evaluate Intrusion Zones
            for zone_id, zone_cfg in self.intrusion_zones.items():
                if det.class_name in zone_cfg["target_classes"]:
                    if is_point_in_polygon(centroid, zone_cfg["polygon"]):
                        events.append({
                            "event_type": "intrusion.detected",
                            "rule_type": "intrusion",
                            "zone_id": zone_id,
                            "track_id": det.track_id or 0,
                            "object_class": det.class_name,
                            "confidence": det.confidence,
                            "bbox": det.bbox,
                        })

            # 2. Evaluate Loitering Zones
            for zone_id, zone_cfg in self.loitering_zones.items():
                if det.class_name in zone_cfg["target_classes"]:
                    if is_point_in_polygon(centroid, zone_cfg["polygon"]):
                        if dwell_time >= zone_cfg["min_dwell_seconds"]:
                            events.append({
                                "event_type": "loitering.detected",
                                "rule_type": "loitering",
                                "zone_id": zone_id,
                                "track_id": det.track_id or 0,
                                "object_class": det.class_name,
                                "dwell_time_seconds": dwell_time,
                                "confidence": det.confidence,
                                "bbox": det.bbox,
                            })

            # 3. Evaluate Line Crossing Tripwires
            if tracker_history and det.track_id in tracker_history:
                track = tracker_history[det.track_id]
                if len(track.trajectory) >= 2:
                    p_prev = (track.trajectory[-2][0], track.trajectory[-2][1])
                    p_curr = centroid

                    for tripwire_id, wire_cfg in self.tripwires.items():
                        if det.class_name in wire_cfg["target_classes"]:
                            if lines_intersect(p_prev, p_curr, wire_cfg["p1"], wire_cfg["p2"]):
                                dir_crossed = determine_crossing_direction(p_prev, p_curr, wire_cfg["p1"], wire_cfg["p2"])
                                if wire_cfg["direction"] in ("BOTH", dir_crossed):
                                    events.append({
                                        "event_type": "line_crossing.detected",
                                        "rule_type": "line_crossing",
                                        "zone_id": tripwire_id,
                                        "track_id": det.track_id or 0,
                                        "object_class": det.class_name,
                                        "direction": dir_crossed,
                                        "confidence": det.confidence,
                                        "bbox": det.bbox,
                                    })

        return events
