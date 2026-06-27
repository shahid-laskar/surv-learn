#!/usr/bin/env python3

from onvif import ONVIFCamera
from zeep.helpers import serialize_object
import pprint
import time

CAMERA_IP = "10.44.0.219"
PORT = 80
USERNAME = "admin"
PASSWORD = "admin"

print(f"Connecting to {CAMERA_IP}...")

cam = ONVIFCamera(
    CAMERA_IP,
    PORT,
    USERNAME,
    PASSWORD
)

events = cam.create_events_service()

print("Creating PullPoint subscription...")
events.CreatePullPointSubscription({
    'InitialTerminationTime': 'PT60M'
})

pullpoint = cam.create_pullpoint_service()

print("Waiting for motion events...")
print("Walk in front of the camera now.")
print("-" * 80)

while True:
    try:
        response = pullpoint.PullMessages({
            "Timeout": "PT10S",
            "MessageLimit": 20
        })

        notifications = response.NotificationMessage or []

        if not notifications:
            print(f"[{time.strftime('%H:%M:%S')}] No events")
            continue

        for n in notifications:
            print("\n" + "=" * 80)
            pprint.pp(serialize_object(n))

    except KeyboardInterrupt:
        print("\nStopped.")
        break

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(2)