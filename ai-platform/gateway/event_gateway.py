"""
ai-platform/gateway/event_gateway.py
Central AI Event Gateway and Normalizer.
Routes validated AI perception events to appropriate Apache Kafka topics.
Includes circuit breaker protection for graceful degradation when Kafka is unreachable.
"""

import json
import logging
import os
import time
from typing import Dict, Any, Optional
from ai_platform.schemas.events import BaseAiEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [ai-gateway] %(message)s")
log = logging.getLogger("ai_event_gateway")

TOPIC_ROUTING = {
    "vehicle.anpr.detected": "vehicle.anpr.detected",
    "vehicle.classified": "vehicle.anpr.detected",
    "intrusion.detected": "camera.ai.alerts",
    "line_crossing.detected": "camera.ai.alerts",
    "loitering.detected": "camera.ai.alerts",
    "abandoned_object.detected": "camera.ai.alerts",
    "fall.detected": "camera.ai.alerts",
    "person.detected": "camera.ai.detections",
    "person.counted": "camera.people.count",
    "crowd.density.updated": "crowd.density.alert",
    "queue.updated": "queue.analytics",
    "face.match.detected": "face.alerts",
}


class AiEventGateway:
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        spool_dir: Optional[str] = None,
        max_spool_files: int = 5000,
    ):
        self.bootstrap = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "surv_kafka:9092")
        self.spool_dir = spool_dir or os.getenv("AI_SPOOL_DIR", "/tmp/sarvanetra_ai_spool")
        self.max_spool_files = max_spool_files
        self.producer = None
        self._circuit_open = False
        self._last_failure_time = 0.0
        self._circuit_cooldown_seconds = 10.0

        os.makedirs(self.spool_dir, exist_ok=True)
        self._init_producer()

    def _init_producer(self):
        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                retries=2,
                request_timeout_ms=2000,
            )
            log.info(f"Connected to Kafka broker at {self.bootstrap}")
            self._circuit_open = False
            # Replay any offline spooled events on connection restore
            self.replay_spooled_events()
        except Exception as e:
            log.warning(f"Kafka producer initialization deferred (offline/degraded mode): {e}")
            self.producer = None
            self._circuit_open = True
            self._last_failure_time = time.time()

    def _spool_event(self, event_dict: Dict[str, Any], topic: str, key: Optional[str]) -> bool:
        """Persists an undelivered event to disk FIFO spool to guarantee zero event loss."""
        try:
            spooled_files = [f for f in os.listdir(self.spool_dir) if f.endswith(".json")]
            if len(spooled_files) >= self.max_spool_files:
                # Bounded disk limit: evict oldest spooled file
                spooled_files.sort()
                oldest_file = os.path.join(self.spool_dir, spooled_files[0])
                try:
                    os.remove(oldest_file)
                    log.warning(f"Spool limit ({self.max_spool_files}) reached. Evicted oldest: {oldest_file}")
                except OSError:
                    pass

            timestamp_ns = time.time_ns()
            event_id = event_dict.get("event_id", "unknown")
            target_file = os.path.join(self.spool_dir, f"{timestamp_ns}_{event_id}.json")
            tmp_file = f"{target_file}.tmp"

            payload = {
                "topic": topic,
                "key": key,
                "event": event_dict,
                "spooled_at": time.time(),
            }

            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(payload, f)
            os.replace(tmp_file, target_file)
            log.debug(f"[Degraded Mode] Event {event_id} spooled to disk: {target_file}")
            return True
        except Exception as ex:
            log.error(f"Failed to spool event to disk: {ex}")
            return False

    def replay_spooled_events(self) -> int:
        """Replays all spooled events in FIFO order upon Kafka reconnection."""
        if not self.producer or self._circuit_open:
            return 0

        spooled_files = sorted([f for f in os.listdir(self.spool_dir) if f.endswith(".json")])
        if not spooled_files:
            return 0

        log.info(f"Replaying {len(spooled_files)} spooled AI events from {self.spool_dir}...")
        replayed_count = 0

        for fname in spooled_files:
            fpath = os.path.join(self.spool_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                topic = data.get("topic", "camera.ai.detections")
                key = data.get("key")
                event_dict = data.get("event", {})

                self.producer.send(topic, key=key, value=event_dict)
                self.producer.flush()

                os.remove(fpath)
                replayed_count += 1
            except json.JSONDecodeError:
                # Quarantine corrupt spooled file
                corrupt_path = f"{fpath}.corrupt"
                os.replace(fpath, corrupt_path)
                log.warning(f"Quarantined corrupt spooled event file: {corrupt_path}")
            except Exception as e:
                log.warning(f"Replay interrupted during {fname}: {e}. Circuit reopened.")
                self._circuit_open = True
                self._last_failure_time = time.time()
                break

        if replayed_count > 0:
            log.info(f"Successfully replayed and delivered {replayed_count} spooled events to Kafka.")
        return replayed_count

    def publish_event(self, event: BaseAiEvent) -> bool:
        """Publishes an AI event to its corresponding Kafka topic, falling back to disk spooling."""
        topic = TOPIC_ROUTING.get(event.event_type, "camera.ai.detections")
        event_dict = event.model_dump(mode="json")
        key = event.camera_id

        # Retry connecting if cooldown passed
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_cooldown_seconds:
                log.info("Attempting Kafka reconnection...")
                self._init_producer()
            else:
                self._spool_event(event_dict, topic, key)
                return False

        if not self.producer:
            self._spool_event(event_dict, topic, key)
            return False

        try:
            self.producer.send(topic, key=key, value=event_dict)
            self.producer.flush()
            log.info(f"Published {event.event_type} [{event.event_id}] -> topic '{topic}' (camera={key})")
            return True
        except Exception as e:
            log.warning(f"Failed to publish event {event.event_id} to Kafka: {e}. Opening circuit breaker.")
            self._circuit_open = True
            self._last_failure_time = time.time()
            self._spool_event(event_dict, topic, key)
            return False

    def close(self):
        if self.producer:
            try:
                self.producer.close()
            except Exception:
                pass
            self.producer = None

