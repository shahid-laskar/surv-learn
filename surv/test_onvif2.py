import sys
from onvif import ONVIFCamera
cam = ONVIFCamera('10.44.0.215', 2020, 'admin', 'Bsnl@695033')
events = cam.create_events_service()
sub = events.CreatePullPointSubscription({'InitialTerminationTime': 'PT60M'})
addr = sub.SubscriptionReference.Address._value_1
print("Subscription address:", addr)
try:
    svc = cam.create_pullpoint_service()
    res = svc.PullMessages({'MessageLimit': 100, 'Timeout': 'PT10S'})
    print("Messages:", len(res.NotificationMessage) if res.NotificationMessage else 0)
except Exception as e:
    print("Error pulling using default pullpoint:", e)
