#!/usr/bin/env python3

from onvif import ONVIFCamera
from zeep.helpers import serialize_object
import pprint

CAMERA_IP = "10.44.0.219"
PORT = 80
USERNAME = "admin"
PASSWORD = "admin"

print(f"Connecting to {CAMERA_IP}...")
cam = ONVIFCamera(CAMERA_IP, PORT, USERNAME, PASSWORD)
events = cam.create_events_service()

print("Fetching Event Properties...")
try:
    props = events.GetEventProperties()
    pprint.pp(serialize_object(props))
except Exception as e:
    print(f"Error fetching event properties: {e}")