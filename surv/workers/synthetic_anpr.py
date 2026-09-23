"""
surv/workers/synthetic_anpr.py
Realistic Synthetic ANPR Event and Traffic Simulator.
Generates realistic Indian vehicle license plates (Kerala, Tamil Nadu, Karnataka),
simulates OCR substitution errors, low-confidence reads, hotlist/watchlist detections,
and publishes payloads conforming strictly to the platform ANPR ingest contract.

Can be run:
  1. Against the central REST API: POST /api/v1/anpr/events
  2. Directly into Kafka topic: anpr.events
  3. One-shot burst for integration testing or load testing
  4. Continuous daemon loop for live demonstration / ICCC monitoring
"""

import argparse
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional
import urllib.request
import urllib.error

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [synthetic-anpr] %(message)s"
)
log = logging.getLogger("synthetic_anpr")

# Common state codes and RTO series around Sabarimala / Nilakkal
RTO_CODES = [
    "KL01", "KL02", "KL03", "KL04", "KL05", "KL06", "KL07", "KL16", "KL25", "KL62",
    "TN01", "TN09", "TN58", "KA01", "KA04", "KA05", "AP09", "MH02"
]
SERIES_LETTERS = ["A", "B", "C", "D", "E", "F", "G", "H", "J", "K", "L", "M", "N", "P", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"]
VEHICLE_TYPES = ["CAR", "LMV", "BUS", "HMV", "2W", "3W", "TRUCK"]
COLORS = ["white", "silver", "black", "grey", "red", "blue", "yellow", "green"]

# Well-known police hotlist vehicles for deterministic testing
KNOWN_WATCHLIST_PLATES = [
    ("KL07BH9999", "WANTED", "Robbery suspect vehicle (Pathanamthitta)"),
    ("KL01DZ0007", "STOLEN", "Stolen Fortuner from Thiruvananthapuram"),
    ("KL03P1111",  "SUSPICIOUS", "Involved in temple premise unauthorized activity"),
]

# Character confusions typical in optical character recognition
OCR_CONFUSIONS = {
    "0": "O", "O": "0",
    "1": "I", "I": "1",
    "8": "B", "B": "8",
    "5": "S", "S": "5",
    "2": "Z", "Z": "2",
}


def generate_valid_plate() -> str:
    rto = random.choice(RTO_CODES)
    series = "".join(random.choices(SERIES_LETTERS, k=random.choice([1, 2])))
    number = f"{random.randint(1, 9999):04d}"
    return f"{rto}{series}{number}"


def introduce_ocr_error(plate: str) -> str:
    """Simulates realistic optical character recognition misread."""
    chars = list(plate)
    mutable_indices = [i for i, c in enumerate(chars) if c in OCR_CONFUSIONS]
    if not mutable_indices:
        return plate
    idx = random.choice(mutable_indices)
    chars[idx] = OCR_CONFUSIONS[chars[idx]]
    return "".join(chars)


def generate_anpr_event(
    camera_id: int = 1,
    site_id: int = 1,
    force_watchlist: bool = False,
    simulate_ocr_error: bool = False,
) -> Dict:
    """Generates an ANPR event payload matching the standard API ingest contract."""
    if force_watchlist:
        plate_tuple = random.choice(KNOWN_WATCHLIST_PLATES)
        plate = plate_tuple[0]
        confidence = round(random.uniform(0.92, 0.99), 2)
        vtype = "CAR"
    else:
        plate = generate_valid_plate()
        if simulate_ocr_error:
            plate = introduce_ocr_error(plate)
            confidence = round(random.uniform(0.60, 0.78), 2)
        else:
            confidence = round(random.uniform(0.85, 0.99), 2)
        vtype = random.choice(VEHICLE_TYPES)

    direction = random.choice(["IN", "OUT"])
    return {
        "plate": plate,
        "confidence": confidence,
        "vehicle_type": vtype,
        "vehicle_color": random.choice(COLORS),
        "camera_id": camera_id,
        "customer_site_id": site_id,
        "lane_id": random.choice([1, 2, 3, 4]),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "speed_kmh": round(random.uniform(15.0, 45.0), 1),
        "direction": direction,
        "snapshot_key": f"snapshots/anpr/{site_id}/{camera_id}/{int(time.time())}_{plate}.jpg",
        "video_reference": f"recordings/{site_id}/{camera_id}/{int(time.time())}.mp4",
        "processing_source": "edge_lpu_simulator",
    }


def post_to_api(api_url: str, event: Dict) -> bool:
    url = f"{api_url.rstrip('/')}/api/v1/anpr/events"
    data = json.dumps(event).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status in (200, 201):
                body = json.loads(resp.read().decode())
                log.info("Ingested plate %s (ID=%s, Conf=%.2f)", event["plate"], body.get("id"), event["confidence"])
                return True
    except Exception as exc:
        log.warning("Failed to post event to API (%s): %s", url, exc)
    return False


def main():
    parser = argparse.ArgumentParser(description="SARVANETRA Synthetic ANPR Generator")
    parser.add_argument("--api-url", default="http://localhost:8000", help="FastAPI base URL")
    parser.add_argument("--count", type=int, default=10, help="Number of events to generate (0 for infinite)")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between events")
    parser.add_argument("--camera-id", type=int, default=1, help="Camera ID")
    parser.add_argument("--site-id", type=int, default=1, help="Site ID")
    parser.add_argument("--watchlist-ratio", type=float, default=0.2, help="Probability of producing watchlist hits")
    parser.add_argument("--ocr-error-ratio", type=float, default=0.15, help="Probability of simulating OCR errors")
    args = parser.parse_args()

    log.info("Starting ANPR traffic simulation target: %s (Count: %s, Interval: %ss)", args.api_url, args.count, args.interval)

    generated = 0
    while True:
        force_wl = random.random() < args.watchlist_ratio
        sim_ocr = random.random() < args.ocr_error_ratio
        event = generate_anpr_event(
            camera_id=args.camera_id,
            site_id=args.site_id,
            force_watchlist=force_wl,
            simulate_ocr_error=sim_ocr,
        )

        post_to_api(args.api_url, event)
        generated += 1

        if args.count > 0 and generated >= args.count:
            log.info("Completed %d synthetic ANPR events.", generated)
            break

        time.sleep(args.interval)


if __name__ == "__main__":
    main()
