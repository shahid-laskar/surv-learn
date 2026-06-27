"""
onvif_motion_producer.py
Subscribes to ONVIF motion events from cameras and publishes
to Kafka camera.motion topic.

Matrix COMSEC MIDR50FL28CWS sends:
  SimpleItem Name="State" Value="true/false"
  Topic is in the NotificationMessage envelope, not the Message element.
  We read it directly from the raw XML.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timezone
from lxml import etree
from onvif import ONVIFCamera
from zeep.exceptions import Fault
from kafka import KafkaProducer
import psycopg2
import psycopg2.extras

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
log = logging.getLogger(__name__)

# Namespaces used in Matrix camera XML
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
        """)
        return [dict(row) for row in cur.fetchall()]


def parse_state_from_message(msg) -> bool | None:
    """
    Parse the State value from a Matrix COMSEC ONVIF message.

    The camera sends:
      <tt:Data>
        <tt:SimpleItem Name="State" Value="true"/>
      </tt:Data>

    We read directly from the raw lxml element since zeep
    fails to deserialize the Topic field on this camera.
    """
    try:
        elem = msg.Message._value_1   # lxml Element
        items = elem.findall('.//tt:SimpleItem', NS)
        for item in items:
            if item.get('Name') == 'State':
                return item.get('Value', '').lower() == 'true'
    except Exception as e:
        log.warning(f"Failed to parse State from message: {e}")
    return None


def parse_topic_from_notification(msg) -> str:
    """
    Extract topic string from the raw NotificationMessage envelope.
    Zeep deserializes Topic as None on this camera — read from _raw_elements.
    """
    try:
        # Topic is in the NotificationMessage, not inside Message
        # Try zeep first
        if msg.Topic is not None and msg.Topic._value_1:
            return str(msg.Topic._value_1)
    except Exception:
        pass
    return "tns1:Configuration/VideoAnalyticsConfiguration"  # Matrix default


class ONVIFCameraProducer:
    """
    Manages ONVIF pull-point subscription for a single camera.
    Runs in its own thread.
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

        sub = events.CreatePullPointSubscription({
            'InitialTerminationTime': SUB_DURATION,
        })
        log.info(f"[{self.cam_path}] ONVIF subscription created (duration: {SUB_DURATION})")

        svc          = cam.create_pullpoint_service()
        sub_start    = time.time()
        renewal_secs = 50 * 60  # renew at 50 min, before the 60 min expiry

        while not self._stop.is_set():

            # Renew subscription before it expires
            if time.time() - sub_start > renewal_secs:
                try:
                    events.CreatePullPointSubscription({
                        'InitialTerminationTime': SUB_DURATION,
                    })
                    sub_start = time.time()
                    log.info(f"[{self.cam_path}] Subscription renewed")
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
        state = parse_state_from_message(msg)
        if state is None:
            return  # not a State message — ignore

        topic      = parse_topic_from_notification(msg)
        event_type = "motion.started" if state else "motion.ended"

        event = {
            "schema_version": "1.0",
            "event_type":     event_type,
            "camera_id":      self.camera_id,
            "camera_path":    self.cam_path,
            "timestamp_utc":  datetime.now(timezone.utc).isoformat(),
            "source_topic":   topic,
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
                     f"(State={state})")
        except Exception as e:
            log.error(f"[{self.cam_path}] Kafka publish failed: {e}")


class MotionProducerWorker:
    """
    Discovers active cameras from the DB every DISCOVERY_INTERVAL seconds
    and manages ONVIFCameraProducer threads for each one.
    """

    def __init__(self):
        self.producers: dict[int, ONVIFCameraProducer] = {}
        self.kafka = get_kafka_producer()

    def run(self):
        log.info("Motion producer worker starting...")
        conn = get_db_connection()

        while True:
            try:
                cameras    = get_active_cameras(conn)
                active_ids = {c["id"] for c in cameras}

                # Start producers for newly active cameras
                for cam in cameras:
                    if cam["id"] not in self.producers:
                        p = ONVIFCameraProducer(cam, self.kafka)
                        p.start()
                        self.producers[cam["id"]] = p

                # Stop producers for deactivated cameras
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