#!/usr/bin/env python3
"""
edge-sim/inject_motion.py
Synthetic motion event injector for edge NVR simulation.

Writes directly to the hub's motion_event table (bypasses Kafka).
Use this to generate realistic motion-event volume for load testing
without needing a real ONVIF stack.

Usage:
  # One-shot burst: inject 5 events for all simulated cameras
  python inject_motion.py --mode burst --sites 3 --cameras-per-site 3 --count 5

  # Continuous: inject events every ~30s forever (Ctrl+C to stop)
  python inject_motion.py --mode continuous --interval 30

  # Single camera, 10 events
  python inject_motion.py --mode burst --camera SIMCAM-SITE01-01 --count 10

Requirements:
  pip install psycopg2-binary python-dotenv
"""

import argparse
import os
import random
import time
from datetime import datetime, timezone, timedelta

try:
    import psycopg2
except ImportError:
    print("Install psycopg2-binary: pip install psycopg2-binary")
    raise

# ── Config ────────────────────────────────────────────────────────────────────
DB_URL = os.environ.get(
    "SYNC_DATABASE_URL",
    "postgresql://surv:surv1234@10.44.0.209:5432/sarvanetra"
)

SIMULATED_CAMERAS = [
    f"SIMCAM-SITE{site:02d}-{cam:02d}"
    for site in range(1, 4)
    for cam in range(1, 4)
]

EVENT_TYPES = ["motion_start", "motion_end", "object_detected", "line_crossed"]
CONFIDENCE_RANGE = (0.60, 0.99)
MOTION_DURATION_RANGE = (3, 45)   # seconds — how long a motion event lasts


# ── DB helpers ────────────────────────────────────────────────────────────────
def get_conn():
    """Return a psycopg2 connection to the hub Postgres."""
    import urllib.parse
    url = DB_URL.replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(url)


def get_camera_ids(conn, cam_ids: list[str]) -> dict[str, int]:
    """Return {cam_id: db_id} for the given cam_id strings."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT cam_id, id FROM survapp_camera_master WHERE cam_id = ANY(%s)",
            (cam_ids,)  # survapp_camera_master confirmed table name
        )
        rows = cur.fetchall()
    return {row[0]: row[1] for row in rows}


def insert_motion_event(conn, camera_id: int, cam_id: str, event_type: str,
                         confidence: float, occurred_at: datetime):
    """Insert one motion_event row into survapp_motion_event."""
    # Schema: camera_id, motion_start, motion_end (nullable), is_active
    duration = random.randint(*MOTION_DURATION_RANGE)
    motion_start = occurred_at
    motion_end = occurred_at + timedelta(seconds=duration) if random.random() > 0.3 else None
    is_active = motion_end is None  # still active if no end time yet

    with conn.cursor() as cur:
        # Get actual column list for survapp_motion_event
        cur.execute(
            """
            INSERT INTO survapp_motion_event
              (camera_id, motion_start, motion_end, is_active, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """,
            (camera_id, motion_start, motion_end, is_active)
        )
    conn.commit()


# ── Main logic ────────────────────────────────────────────────────────────────
def inject_events(cameras: list[str], count: int, verbose: bool = True):
    """Inject `count` random motion events across the given cameras."""
    conn = get_conn()
    id_map = get_camera_ids(conn, cameras)

    missing = set(cameras) - set(id_map.keys())
    if missing:
        print(f"[warn] Not found in DB (not registered yet?): {missing}")
        cameras = [c for c in cameras if c in id_map]

    if not cameras:
        print("[err]  No valid cameras to inject into. Run setup_sim.sh first.")
        conn.close()
        return 0

    injected = 0
    for _ in range(count):
        cam_id = random.choice(cameras)
        db_id = id_map[cam_id]
        evt_type = random.choice(EVENT_TYPES)
        confidence = random.uniform(*CONFIDENCE_RANGE)
        # Slightly randomise timestamp to simulate realistic spread
        occurred_at = datetime.now(timezone.utc) - timedelta(seconds=random.randint(0, 5))

        try:
            insert_motion_event(conn, db_id, cam_id, evt_type, confidence, occurred_at)
            injected += 1
            if verbose:
                print(f"  [+] {cam_id:30s}  motion event  @ {occurred_at.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"  [!] Failed for {cam_id}: {e}")

    conn.close()
    return injected


def build_camera_list(args) -> list[str]:
    """Build the list of cameras to inject into based on CLI args."""
    if args.camera:
        return [args.camera]

    sites = range(1, args.sites + 1)
    cams_per_site = range(1, args.cameras_per_site + 1)
    return [f"SIMCAM-SITE{s:02d}-{c:02d}" for s in sites for c in cams_per_site]


def main():
    parser = argparse.ArgumentParser(description="Sarvanetra sim motion event injector")
    parser.add_argument("--mode", choices=["burst", "continuous"], default="burst",
                        help="burst: inject N events and exit; continuous: inject every --interval seconds")
    parser.add_argument("--camera", default=None,
                        help="Single camera ID (e.g. SIMCAM-SITE01-01). Overrides --sites/--cameras-per-site.")
    parser.add_argument("--sites", type=int, default=3,
                        help="Number of simulated sites (1..N, default 3)")
    parser.add_argument("--cameras-per-site", type=int, default=3,
                        help="Cameras per site (default 3)")
    parser.add_argument("--count", type=int, default=10,
                        help="Events to inject per burst (default 10)")
    parser.add_argument("--interval", type=float, default=30.0,
                        help="Seconds between bursts in continuous mode (default 30)")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-event output")
    args = parser.parse_args()

    cameras = build_camera_list(args)
    print(f"[sim] Target cameras ({len(cameras)}): {', '.join(cameras[:6])}{'...' if len(cameras)>6 else ''}")
    print(f"[sim] DB: {DB_URL.split('@')[-1]}")
    print()

    if args.mode == "burst":
        n = inject_events(cameras, args.count, verbose=not args.quiet)
        print(f"\n[done] Injected {n} motion events.")

    else:  # continuous
        print(f"[sim] Continuous mode — injecting {args.count} events every {args.interval}s. Ctrl+C to stop.\n")
        total = 0
        try:
            while True:
                n = inject_events(cameras, args.count, verbose=not args.quiet)
                total += n
                print(f"[sim] Burst done ({n} events). Total so far: {total}. "
                      f"Next in {args.interval}s...")
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print(f"\n[sim] Stopped. Total injected: {total}")


if __name__ == "__main__":
    main()
