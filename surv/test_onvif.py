from onvif import ONVIFCamera
cam = ONVIFCamera('10.44.0.215', 2020, 'admin', 'admin')
events = cam.create_events_service()
sub = events.CreatePullPointSubscription({'InitialTerminationTime': 'PT60M'})
addr = sub.SubscriptionReference.Address._value_1
print("Subscription address:", addr)
