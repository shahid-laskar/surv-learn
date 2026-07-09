#!/usr/bin/env python3
"""Register simulated cameras on the hub and assign them to an NVR site."""

import argparse
import os
import sys

import httpx

HUB_API = os.environ.get("HUB_API_URL", "http://10.44.0.209:8000/api/v1").rstrip("/")
ADMIN_USER = os.environ.get("HUB_ADMIN_USER", "admin")
ADMIN_PASS = os.environ.get("HUB_ADMIN_PASS", "admin123")


def login(client: httpx.Client) -> str:
    r = client.post(
        f"{HUB_API}/auth/login",
        json={"username": ADMIN_USER, "password": ADMIN_PASS},
    )
    r.raise_for_status()
    return r.json()["access_token"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", default="SITE01", help="NVR site code")
    parser.add_argument("--sites", type=int, default=1, help="Number of sites (1-3)")
    args = parser.parse_args()

    cameras = []
    for site in range(1, args.sites + 1):
        site_code = f"SITE{site:02d}"
        for cam in range(1, 4):
            cam_id = f"SIMCAM-{site_code}-0{cam}"
            cameras.append(
                {
                    "cam_id": cam_id,
                    "cam_name": f"Sim {site_code} Cam 0{cam}",
                    "cam_ip": f"127.0.0.{site}{cam}",
                    "cam_port": 554,
                    "rtsp_url": f"rtsp://mediamtx:8554/{cam_id}",
                    "onvif_username": "admin",
                    "onvif_password": "admin",
                    "motion_active": True,
                    "retention_days": 7,
                }
            )

    with httpx.Client(timeout=30) as client:
        token = login(client)
        headers = {"Authorization": f"Bearer {token}"}

        for cam in cameras:
            r = client.post(f"{HUB_API}/cameras/", json=cam, headers=headers)
            if r.status_code == 409:
                print(f"exists: {cam['cam_id']}")
            else:
                r.raise_for_status()
                print(f"created: {cam['cam_id']}")

        site_code = args.site
        for cam in cameras:
            if not cam["cam_id"].startswith(f"SIMCAM-{site_code}"):
                continue
            r = client.post(
                f"{HUB_API}/fleet/{site_code}/cameras",
                json={"cam_id": cam["cam_id"]},
                headers=headers,
            )
            if r.status_code in (200, 201):
                print(f"assigned {cam['cam_id']} -> {site_code}")
            else:
                print(f"assign failed {cam['cam_id']}: {r.status_code} {r.text[:120]}", file=sys.stderr)


if __name__ == "__main__":
    main()
