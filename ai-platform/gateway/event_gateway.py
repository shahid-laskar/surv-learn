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
    def __init__(self, bootstrap_servers: Optional[str] = None):
        self.bootstrap = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "surv_kafka:9092")
        self.producer = None
        self._circuit_open = False
        self._last_failure_time = 0.0
        self._circuit_cooldown_seconds = 10.0
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
        except Exception as e:
            log.warning(f"Kafka producer initialization deferred (offline/degraded mode): {e}")
            self.producer = None
            self._circuit_open = True
            self._last_failure_time = time.time()

    def publish_event(self, event: BaseAiEvent) -> bool:
        """Publishes an AI event to its corresponding Kafka topic."""
        topic = TOPIC_ROUTING.get(event.event_type, "camera.ai.detections")
        event_dict = event.model_dump(mode="json")
        key = event.camera_id

        # Retry connecting if cooldown passed
        if self._circuit_open:
            if time.time() - self._last_failure_time > self._circuit_cooldown_seconds:
                log.info("Attempting Kafka reconnection...")
                self._init_producer()
            else:
                log.debug(f"[Degraded Mode] Event {event.event_id} ({event.event_type}) recorded locally (Kafka circuit open)")
                return False

        if not self.producer:
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
            return False

    def close(self):
        if self.producer:
            try:
                self.producer.close()
            except Exception:
                pass
            self.producer = None
