"""
onvif_motion_producer.py
Subscribes to ONVIF motion events from cameras (any Profile S compliant
vendor — Matrix, TP-Link, CP Plus, Hikvision-OEM, Dahua-OEM, Axis, etc.)
and publishes normalized events to the Kafka camera.motion topic.

VENDOR NOTES
------------
Different ONVIF stacks disagree on two things: where the "this is a
motion event" signal lives, and what the boolean state key is called.

  * Well-behaved cameras (CP Plus, Hikvision-OEM, Dahua-OEM, Axis, ...)
    populate the WS-Notification <Topic> element correctly. zeep
    deserializes it fine, and the topic looks like:
        tns1:RuleEngine/CellMotionDetector/Motion
        tns1:VideoSource/MotionAlarm
    The boolean lives in a SimpleItem named "State".

  * Matrix COMSEC MIDR50FL28CWS and TP-Link VIGI C330I both leave Topic
    as None after zeep deserialization. They put a "Rule" SimpleItem in
    the message body instead (Rule="MotionInDefinedCells" /
    "MyMotionDetectorRule") and the boolean is named "IsMotion".

Rather than hard-coding per-vendor branches, parse_motion_event() below
tries the standard (topic-based) route first and only falls back to the
rule-based body inspection when the topic is unusable.

Also: python-onvif-zeep creates a PullPointSubscription during
ONVIFCamera.__init__. Any later CreatePullPointSubscription returns a
*different* URL (TP-Link uses a fresh high port each time). We must
rebind cam.xaddrs before create_pullpoint_service() or PullMessages
hits the dead init subscription.

We deliberately do NOT treat "any State/IsMotion key we see" as a motion
event — cameras reuse those same key names for tamper detection, line
crossing, audio alarms, etc. We only extract state after confirming
(via topic or rule) that the message *is* a motion event, so we don't
generate false motion.started/ended events from unrelated analytics.

Known limitation: some consumer-grade cameras (e.g. TP-Link Tapo) only
implement a partial ONVIF profile and don't support PullPointSubscription
at all. Those need a vendor SDK/RTSP-side motion approach instead — this
producer only covers Profile S / event-service-compliant devices.
"""

import os
import json
import time
import logging
import threading
import ipaddress
from datetime import datetime, timezone
from lxml import etree
from onvif import ONVIFCamera
from zeep.exceptions import Fault
from kafka import KafkaProducer
import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)
# Quieten verbose libraries
logging.getLogger("kafka").setLevel(logging.WARNING)
logging.getLogger("zeep").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Namespaces used across ONVIF camera XML (vendor-agnostic — part of the spec)
NS = {
    'tt':    'http://www.onvif.org/ver10/schema',
    'wsnt':  'http://docs.oasis-open.org/wsn/b-2',
    'tns1':  'http://www.onvif.org/ver10/topics',
    'wstop': 'http://docs.oasis-open.org/wsn/t-1',
}

DB_URL             = os.getenv("DATABASE_URL",           "postgresql://surv:changeme@postgres:5432/sarvanetra")
KAFKA_BOOTSTRAP    = os.getenv("KAFKA_BOOTSTRAP_SERVERS","kafka:9092")
ONVIF_USERNAME     = os.getenv("ONVIF_USERNAME",         "admin")
ONVIF_PASSWORD     = os.getenv("ONVIF_PASSWORD",         "admin")
ONVIF_PORT         = int(os.getenv("ONVIF_PORT",         "80"))
PULL_TIMEOUT_SECS  = int(os.getenv("ONVIF_PULL_TIMEOUT", "10"))
SUB_DURATION       = os.getenv("ONVIF_SUB_DURATION",     "PT60M")
DISCOVERY_INTERVAL = int(os.getenv("DISCOVERY_INTERVAL_SECONDS", "60"))

# ── Motion classification constants (data-driven, extend as new vendors surface) ──

# Substrings that indicate a Topic is a motion topic. Lower-cased match.
# Covers: tns1:RuleEngine/CellMotionDetector/Motion, tns1:VideoSource/MotionAlarm,
# tns1:RuleEngine/MotionRegionDetector/Motion, etc.
MOTION_TOPIC_KEYWORDS = (
    "cellmotiondetector",
    "motionregiondetector",
    "motionalarm",
    "motiondetector",
)

# "Rule" SimpleItem values that mean "this is a motion rule" — used only when
# Topic is missing/unreliable (e.g. Matrix / TP-Link VIGI broken Topic
# deserialization). Exact match first; keyword substring covers vendor-specific
# names like TP-Link's "MyMotionDetectorRule".
MOTION_RULE_NAMES = {
    "motionindefinedcells",
    "motiondetection",
    "motion",
    "cellmotiondetector",
    "motionalarm",
    "motionregiondetector",
    "mymotiondetectorrule",
}
MOTION_RULE_KEYWORDS = ("motion",)

# Boolean state key names, in priority order. "State" is the ONVIF-standard
# name used by most vendors; "IsMotion" is Matrix/TP-Link's non-standard variant.
MOTION_STATE_KEYS = ("State", "IsMotion", "Motion")

# NS used by python-onvif-zeep for the PullPointSubscription XAddr key.
# ONVIFCamera.__init__ already creates one subscription and stores its address
# here; if we CreatePullPointSubscription again we MUST overwrite this before
# create_pullpoint_service(), or PullMessages hits a stale/dead endpoint.
PULLPOINT_NS = "http://www.onvif.org/ver10/events/wsdl/PullPointSubscription"


def get_kafka_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8"),
        retries=5,
        acks="all",
    )


def get_db_connection():
    return psycopg2.connect(DB_URL)


def is_onvif_target(camera: dict) -> bool:
    """
    Return True if the hub can reach this camera's ONVIF endpoint.

    Simulated edge cameras are registered with 127.0.0.x "LAN" IPs that only
    exist inside the edge NVR — the hub ONVIF producer must not poll them.
    """
    ip_str = (camera.get("cam_ip") or "").strip()
    if not ip_str:
        return False
    try:
        addr = ipaddress.ip_address(ip_str)
    except ValueError:
        log.warning(f"[{camera.get('cam_id')}] Invalid cam_ip={ip_str!r} — skipping ONVIF")
        return False
    if addr.is_loopback:
        return False
    return True


def get_active_cameras(conn) -> list[dict]:
    """
    Query cameras that are active and have motion detection enabled.
    Returns list of dicts with id, cam_id, cam_ip fields.
    """
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("""
            SELECT id, cam_id, cam_ip, onvif_port, onvif_username, onvif_password
            FROM survapp_camera_master
            WHERE is_active = true
              AND motion_active = true
              AND nvr_node_id IS NULL
        """)
        return [dict(row) for row in cur.fetchall()]


def _extract_topic(msg) -> str | None:
    """
    Try to pull the WS-Notification Topic string off the message.
    Returns None if zeep failed to deserialize it (happens on Matrix and
    TP-Link VIGI) rather than guessing a default.
    """
    try:
        if msg.Topic is not None and msg.Topic._value_1 is not None:
            topic = str(msg.Topic._value_1).strip()
            return topic or None
    except Exception:
        pass
    return None


def _extract_simple_items(msg) -> dict:
    """Flatten the tt:SimpleItem Name/Value pairs out of the message body."""
    try:
        elem = msg.Message._value_1  # lxml Element
        items = elem.findall('.//tt:SimpleItem', NS)
        return {item.get('Name'): item.get('Value') for item in items}
    except Exception as e:
        log.warning(f"Failed to extract SimpleItems: {e}")
        return {}


def _is_motion_rule(rule: str) -> bool:
    """True if a Rule SimpleItem value identifies a motion detector."""
    if not rule:
        return False
    if rule in MOTION_RULE_NAMES:
        return True
    return any(kw in rule for kw in MOTION_RULE_KEYWORDS)


def parse_motion_event(msg) -> tuple[bool, str] | None:
    """
    Universal ONVIF motion parser.

    Returns (is_motion: bool, topic_or_rule: str) if this message is a
    motion event, or None if it isn't (tamper, line-crossing, audio,
    recording-state, etc. all get filtered out here).

    Classification order:
      1. Topic-based (standard path) — Profile-S cameras with a usable Topic.
      2. Rule-based fallback — Topic missing/unusable (Matrix COMSEC,
         TP-Link VIGI C330I, etc.).
    """
    item_data = _extract_simple_items(msg)
    if not item_data:
        return None

    topic = _extract_topic(msg)
    classified_as_motion = False
    label = topic

    if topic is not None:
        topic_lower = topic.lower()
        classified_as_motion = any(kw in topic_lower for kw in MOTION_TOPIC_KEYWORDS)
    else:
        # Topic unusable — fall back to inspecting the Rule SimpleItem.
        rule = (item_data.get('Rule') or '').lower()
        if _is_motion_rule(rule):
            classified_as_motion = True
            label = f"rule:{rule}"

    if not classified_as_motion:
        log.debug(f"Ignoring non-motion message (topic={topic}, items={item_data})")
        return None

    for key in MOTION_STATE_KEYS:
        if key in item_data:
            return item_data[key].lower() == 'true', label

    log.warning(f"Motion message classified but no state key found: {item_data}")
    return None


def _subscription_address(sub) -> str:
    addr = sub.SubscriptionReference.Address
    return str(getattr(addr, '_value_1', addr))


def _bind_pullpoint_service(cam: ONVIFCamera, sub) -> object:
    """
    Point PullMessages at the subscription we just created.

    python-onvif-zeep's ONVIFCamera.update_xaddrs() already opens a pull-point
    during __init__. CreatePullPointSubscription() then opens a *second* one
    with a different URL (TP-Link VIGI uses a fresh high port each time).
    create_pullpoint_service() reads cam.xaddrs[PULLPOINT_NS], so without this
    rebind PullMessages hits the dead init subscription and the camera resets
    the TCP connection.
    """
    cam.xaddrs[PULLPOINT_NS] = _subscription_address(sub)
    with cam.services_lock:
        cam.services.pop('pullpoint', None)
        if hasattr(cam, 'pullpoint'):
            delattr(cam, 'pullpoint')
    return cam.create_pullpoint_service()


class ONVIFCameraProducer:
    """
    Manages ONVIF pull-point subscription for a single camera.
    Runs in its own thread. Vendor-agnostic — any Profile S device that
    exposes CreatePullPointSubscription / PullMessages works here.
    """

    def __init__(self, camera: dict, kafka: KafkaProducer):
        self.camera    = camera
        self.kafka     = kafka
        self.camera_id = camera["id"]
        self.cam_path  = camera["cam_id"]
        self.cam_ip    = camera["cam_ip"]
        self.port      = int(camera.get("onvif_port") or ONVIF_PORT)
        self.username  = camera.get("onvif_username") or ONVIF_USERNAME
        self.password  = camera.get("onvif_password") or ONVIF_PASSWORD
        self._stop     = threading.Event()
        self._thread   = None

    def start(self):
        self._thread = threading.Thread(
            target=self._run,
            name=f"onvif-{self.cam_path}",
            daemon=True,
        )
        self._thread.start()
        log.info(f"[{self.cam_path}] Producer thread started")

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.is_set():
            try:
                self._subscribe_and_pull()
            except Exception as e:
                log.error(f"[{self.cam_path}] Producer error: {e}")
                log.info(f"[{self.cam_path}] Retrying in 30s...")
                time.sleep(30)

    def _subscribe_and_pull(self):
        log.info(f"[{self.cam_path}] Connecting to {self.cam_ip}:{self.port}")
        cam    = ONVIFCamera(self.cam_ip, self.port, self.username, self.password)
        events = cam.create_events_service()

        # Create our own subscription (with controlled duration), then rebind
        # pullpoint XAddr. ONVIFCamera.__init__ already opened one during
        # update_xaddrs(); without rebinding, PullMessages hits that stale
        # URL (TP-Link VIGI: connection reset / no events).
        sub = events.CreatePullPointSubscription({
            'InitialTerminationTime': SUB_DURATION,
        })
        svc = _bind_pullpoint_service(cam, sub)
        log.info(
            f"[{self.cam_path}] ONVIF subscription created "
            f"(duration: {SUB_DURATION}, pullpoint: {cam.xaddrs.get(PULLPOINT_NS)})"
        )

        sub_start    = time.time()
        renewal_secs = 50 * 60  # renew at 50 min, before the 60 min expiry

        while not self._stop.is_set():

            # Renew subscription before it expires — must rebind pullpoint URL
            if time.time() - sub_start > renewal_secs:
                try:
                    sub = events.CreatePullPointSubscription({
                        'InitialTerminationTime': SUB_DURATION,
                    })
                    svc = _bind_pullpoint_service(cam, sub)
                    sub_start = time.time()
                    log.info(
                        f"[{self.cam_path}] Subscription renewed "
                        f"(pullpoint: {cam.xaddrs.get(PULLPOINT_NS)})"
                    )
                except Exception as e:
                    log.warning(f"[{self.cam_path}] Renewal failed: {e}")

            try:
                response = svc.PullMessages({
                    'MessageLimit': 100,
                    'Timeout': f'PT{PULL_TIMEOUT_SECS}S',
                })
            except Fault as e:
                log.warning(f"[{self.cam_path}] SOAP fault — resubscribing: {e}")
                break  # break inner loop → outer loop resubscribes
            except Exception as e:
                log.error(f"[{self.cam_path}] PullMessages error: {e}")
                time.sleep(5)
                continue

            for msg in (response.NotificationMessage or []):
                self._process_message(msg)

    def _process_message(self, msg):
        # ── Dump the raw XML so we can see what a new/unknown camera sends ──
        try:
            raw_elem = msg.Message._value_1
            raw_xml = etree.tostring(raw_elem, pretty_print=True).decode()
            log.debug(f"[{self.cam_path}] RAW Message XML:\n{raw_xml}")
        except Exception as dump_err:
            log.debug(f"[{self.cam_path}] Could not dump raw XML: {dump_err}")

        try:
            log.debug(f"[{self.cam_path}] Topic: {msg.Topic}")
        except Exception:
            pass

        result = parse_motion_event(msg)
        if result is None:
            return  # not a motion event — ignore

        state, classified_via = result
        event_type = "motion.started" if state else "motion.ended"

        event = {
            "schema_version": "1.0",
            "event_type":     event_type,
            "camera_id":      self.camera_id,
            "camera_path":    self.cam_path,
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
            "source_topic":   classified_via,
            "is_motion":      state,
        }

        try:
            self.kafka.send(
                "camera.motion",
                key=str(self.camera_id),
                value=event,
            )
            self.kafka.flush()
            log.info(f"[{self.cam_path}] Published: {event_type} "
                     f"(State={state}, via={classified_via})")
        except Exception as e:
            log.error(f"[{self.cam_path}] Kafka publish failed: {e}")


class MotionProducerWorker:
    """
    Discovers active cameras from the DB every DISCOVERY_INTERVAL seconds
    and manages ONVIFCameraProducer threads for each one.
    """

    def __init__(self):
        self.producers: dict[int, ONVIFCameraProducer] = {}
        self._skipped_logged: set[int] = set()
        self.kafka = get_kafka_producer()

    def run(self):
        log.info("Motion producer worker starting...")
        conn = get_db_connection()

        while True:
            try:
                cameras    = get_active_cameras(conn)
                onvif_cams = [c for c in cameras if is_onvif_target(c)]
                active_ids = {c["id"] for c in onvif_cams}

                for cam in cameras:
                    if is_onvif_target(cam):
                        continue
                    if cam["id"] not in self._skipped_logged:
                        log.info(
                            f"[{cam['cam_id']}] Skipping ONVIF — "
                            f"unreachable sim/loopback IP {cam['cam_ip']}"
                        )
                        self._skipped_logged.add(cam["id"])

                # Start producers for newly active cameras
                for cam in onvif_cams:
                    if cam["id"] not in self.producers:
                        p = ONVIFCameraProducer(cam, self.kafka)
                        p.start()
                        self.producers[cam["id"]] = p

                # Stop producers for deactivated or skipped cameras
                for cam_id in list(self.producers):
                    if cam_id not in active_ids:
                        self.producers[cam_id].stop()
                        del self.producers[cam_id]
                        log.info(f"Stopped producer for camera_id={cam_id}")

            except psycopg2.OperationalError:
                log.error("DB connection lost — reconnecting...")
                try:
                    conn = get_db_connection()
                except Exception as e:
                    log.error(f"DB reconnect failed: {e}")
            except Exception as e:
                log.error(f"Discovery error: {e}")

            time.sleep(DISCOVERY_INTERVAL)


if __name__ == "__main__":
    worker = MotionProducerWorker()
    worker.run()