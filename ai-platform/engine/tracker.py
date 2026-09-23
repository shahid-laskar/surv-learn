"""
ai-platform/engine/tracker.py
Lightweight Permissive Multi-Object Tracker.
Implements centroid-IoU spatial association (MIT-licensed ByteTrack principles).
Assigns persistent track IDs, maintains temporal trajectories, and computes dwell time.
"""

import math
import time
from typing import List, Dict, Tuple, Optional
from ai_platform.engine.base import BaseTracker, Detection


def calculate_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
    """Calculates Intersection-over-Union between two bounding boxes (x1, y1, x2, y2)."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = max(0.0, boxA[2] - boxA[0]) * max(0.0, boxA[3] - boxA[1])
    boxBArea = max(0.0, boxB[2] - boxB[0]) * max(0.0, boxB[3] - boxB[1])

    union = boxAArea + boxBArea - interArea
    if union <= 0.0:
        return 0.0
    return interArea / union


class Track:
    def __init__(self, track_id: int, detection: Detection, start_time: float):
        self.track_id = track_id
        self.class_name = detection.class_name
        self.confidence = detection.confidence
        self.bbox = detection.bbox
        self.centroid = detection.centroid
        self.start_time = start_time
        self.last_seen = start_time
        self.trajectory: List[Tuple[float, float, float]] = [(detection.centroid[0], detection.centroid[1], start_time)]
        self.disappeared_count = 0

    @property
    def dwell_time_seconds(self) -> float:
        return max(0.0, self.last_seen - self.start_time)

    def update(self, detection: Detection, timestamp: float):
        self.class_name = detection.class_name
        self.confidence = detection.confidence
        self.bbox = detection.bbox
        self.centroid = detection.centroid
        self.last_seen = timestamp
        self.disappeared_count = 0
        self.trajectory.append((self.centroid[0], self.centroid[1], timestamp))
        if len(self.trajectory) > 50:
            self.trajectory.pop(0)


class ByteTracker(BaseTracker):
    """
    Two-stage association tracker inspired by ByteTrack.
    Stage 1: Match high-confidence detections with active tracks using IoU.
    Stage 2: Match remaining tracks with lower-confidence detections or nearest centroid.
    """

    def __init__(
        self,
        high_conf_thresh: float = 0.6,
        low_conf_thresh: float = 0.2,
        iou_thresh: float = 0.25,
        max_disappeared: int = 15,
    ):
        self.high_conf_thresh = high_conf_thresh
        self.low_conf_thresh = low_conf_thresh
        self.iou_thresh = iou_thresh
        self.max_disappeared = max_disappeared

        self.next_track_id = 1
        self.tracks: Dict[int, Track] = {}

    def update(self, detections: List[Detection], frame_timestamp: Optional[float] = None) -> List[Detection]:
        if frame_timestamp is None:
            frame_timestamp = time.time()

        # Separate detections into high confidence and low confidence
        high_dets = [d for d in detections if d.confidence >= self.high_conf_thresh]
        low_dets = [d for d in detections if self.low_conf_thresh <= d.confidence < self.high_conf_thresh]

        unmatched_tracks = set(self.tracks.keys())
        unmatched_dets = []

        # Stage 1: Match high-confidence detections
        for det in high_dets:
            best_track_id = None
            best_iou = self.iou_thresh

            for track_id in unmatched_tracks:
                track = self.tracks[track_id]
                if track.class_name != det.class_name:
                    continue
                iou = calculate_iou(track.bbox, det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id

            if best_track_id is not None:
                self.tracks[best_track_id].update(det, frame_timestamp)
                det.track_id = best_track_id
                det.attributes["dwell_time"] = self.tracks[best_track_id].dwell_time_seconds
                unmatched_tracks.remove(best_track_id)
            else:
                unmatched_dets.append(det)

        # Stage 2: Match remaining tracks with low-confidence detections
        for det in low_dets:
            best_track_id = None
            best_iou = self.iou_thresh

            for track_id in list(unmatched_tracks):
                track = self.tracks[track_id]
                if track.class_name != det.class_name:
                    continue
                iou = calculate_iou(track.bbox, det.bbox)
                if iou > best_iou:
                    best_iou = iou
                    best_track_id = track_id

            if best_track_id is not None:
                self.tracks[best_track_id].update(det, frame_timestamp)
                det.track_id = best_track_id
                det.attributes["dwell_time"] = self.tracks[best_track_id].dwell_time_seconds
                unmatched_tracks.remove(best_track_id)

        # Create new tracks for unmatched high-confidence detections
        for det in unmatched_dets:
            new_id = self.next_track_id
            self.next_track_id += 1
            new_track = Track(new_id, det, frame_timestamp)
            self.tracks[new_id] = new_track
            det.track_id = new_id
            det.attributes["dwell_time"] = 0.0

        # Mark disappeared tracks and evict stale ones
        for track_id in unmatched_tracks:
            self.tracks[track_id].disappeared_count += 1
            if self.tracks[track_id].disappeared_count > self.max_disappeared:
                del self.tracks[track_id]

        return [d for d in detections if d.track_id is not None]

    def reset(self) -> None:
        self.tracks.clear()
        self.next_track_id = 1
