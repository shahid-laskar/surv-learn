import time
import pprint
from zeep.helpers import serialize_object
from onvif import ONVIFCamera
from lxml import etree

CAMERA_IP = "10.44.0.219"
PORT = 80
USERNAME = "admin"
PASSWORD = "admin"

cam = ONVIFCamera(CAMERA_IP, PORT, USERNAME, PASSWORD)
events = cam.create_events_service()

sub = events.CreatePullPointSubscription({
    'InitialTerminationTime': 'PT10M',
})
print("Subscription created.")
svc = cam.create_pullpoint_service()

for i in range(3):
    print("Pulling messages...")
    response = svc.PullMessages({
        'MessageLimit': 10,
        'Timeout': 'PT5S',
    })
    msgs = response.NotificationMessage or []
    print(f"Got {len(msgs)} messages.")
    for msg in msgs:
        print("Message:")
        pprint.pp(serialize_object(msg))
        
        # also print raw xml to see how it looks
        if hasattr(msg.Message, '_value_1'):
            elem = msg.Message._value_1
            print("Raw XML:")
            print(etree.tostring(elem, pretty_print=True).decode())
            
    time.sleep(2)
