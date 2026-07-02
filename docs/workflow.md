#start testing mediamtx
docker run --rm \
  --network surv_surv_net \
  jrottenberg/ffmpeg:4.4-alpine \
  -re \
  -f lavfi -i testsrc2=size=1280x720:rate=25 \
  -c:v libx264 \
  -preset ultrafast \
  -tune zerolatency \
  -pix_fmt yuv420p \
  -f rtsp \
  rtsp://mediamtx:8554/cam_test

  #separate tab
  curl http://localhost:9997/v3/paths/list

  source .env && docker compose exec minio sh -c \
  "mc alias set local http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && mc ls --recursive local/recordings/"

   source .env && docker compose exec minio sh -c \
  "mc alias set local http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && mc ls --recursive local/recordings/"| grep "\.mp4" | wc -l

  source .env && docker compose exec minio sh -c \
  "mc alias set local http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && mc cat \
  local/recordings/CAMKRTVM00001/2026/06/25/11-07-32-573413.json"
  source .env && docker compose exec minio sh -c \
  "mc alias set local http://localhost:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD} && mc ls --recursive local/snapshots/"


##KAFKA
Step 1 — Add Kafka variables to .env
  # .env — add these lines
KAFKA_PORT=9092
KAFKA_UI_PORT=8090


Step 2 — Add Kafka to docker-compose.yml
kafka:
    image: apache/kafka:3.7.0
    container_name: surv_kafka
    restart: unless-stopped
    networks:
      - surv_net
    ports:
      - "${KAFKA_PORT}:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@surv_kafka:9093
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://surv_kafka:9092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      CLUSTER_ID: 5L6g3nShT-eMCtK--X86sw
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092 --list || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s

  kafka_init:
    image: apache/kafka:3.7.0
    container_name: surv_kafka_init
    restart: "no"
    networks:
      - surv_net
    depends_on:
      kafka:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
        /opt/kafka/bin/kafka-topics.sh --bootstrap-server surv_kafka:9092 --create --if-not-exists --topic camera.motion --partitions 3 --replication-factor 1;
        /opt/kafka/bin/kafka-topics.sh --bootstrap-server surv_kafka:9092 --create --if-not-exists --topic camera.status --partitions 3 --replication-factor 1;
        /opt/kafka/bin/kafka-topics.sh --bootstrap-server surv_kafka:9092 --create --if-not-exists --topic recording.segments --partitions 3 --replication-factor 1;
        /opt/kafka/bin/kafka-topics.sh --bootstrap-server surv_kafka:9092 --list;
      "

  kafka_ui:
    image: provectuslabs/kafka-ui:latest
    container_name: surv_kafka_ui
    restart: unless-stopped
    networks:
      - surv_net
    ports:
      - "${KAFKA_UI_PORT}:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: surv
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      kafka:
        condition: service_healthy

  mediamtx:
    build:
      context: .
      dockerfile: Dockerfile.mediamtx
    container_name: surv_mediamtx
    restart: unless-stopped
    environment:
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ROOT_USER}
      MINIO_SECRET_KEY: ${MINIO_ROOT_PASSWORD}
      MINIO_BUCKET: recordings
      SEGMENT_DURATION_SECONDS: ${SEGMENT_DURATION_SECONDS}
    networks:
      - surv_net
    ports:
      - "${MEDIAMTX_RTSP_PORT}:8554"
      - "${MEDIAMTX_HLS_PORT}:8888"
      - "${MEDIAMTX_WEBRTC_PORT}:8889"
      - "8189:8189/udp"
      - "${MEDIAMTX_API_PORT}:9997"
    volumes:
      - ./mediamtx/mediamtx.yml:/mediamtx.yml:ro
      - hls_segments:/var/hls
      - ./recordings:/recordings
      - ./scripts:/scripts
      - ./workers/upload_to_minio.py:/app/upload_to_minio.py:ro
      - ./workers/test_presign.py:/app/test_presign.py:ro


Step 3 — Start Kafka and verify
docker compose up -d kafka
docker compose logs -f kafka
Once healthy, create the topics:

docker compose up kafka_init
docker compose logs kafka_init

#expected output
Created topic camera.motion.
Created topic camera.status.
Created topic recording.segments.
Kafka topics created
camera.motion
camera.status
recording.segments

see topics 
docker compose exec kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 \
  --list

  or in url : http://10.44.0.209:8090

Step 4 — Verify produce and consume manually
# Produce a test message to camera.motion

# Sarvanetra Kafka Final Validation

## 1. Verify Kafka Health

```bash
docker compose ps
docker compose logs kafka | tail -50
```

Expected:

* Kafka container is `healthy`
* No ERROR or FATAL messages.

---

## 2. Verify Topics

```bash
docker compose exec kafka \
/opt/kafka/bin/kafka-topics.sh \
--bootstrap-server localhost:9092 \
--list
```

Expected topics:

```text
camera.motion
camera.status
recording.segments
```

---

## 3. Produce Test Message

```bash
echo '{"camera_id":"CAMKRTVM00001","event":"motion_detected","timestamp":"2026-06-27T12:00:00Z"}' | \
docker compose exec -T kafka \
/opt/kafka/bin/kafka-console-producer.sh \
--bootstrap-server localhost:9092 \
--topic camera.motion
```

---

## 4. Verify Offsets

```bash
docker compose exec kafka \
/opt/kafka/bin/kafka-get-offsets.sh \
--bootstrap-server localhost:9092 \
--topic camera.motion
```

Expected:
At least one partition offset should increase.

Example:

```text
camera.motion:0:2
camera.motion:1:0
camera.motion:2:1
```

---

## 5. Consume Messages

```bash
docker compose exec -T kafka \
/opt/kafka/bin/kafka-console-consumer.sh \
--bootstrap-server localhost:9092 \
--topic camera.motion \
--partition 0 \
--offset earliest \
--max-messages 10
```

Expected:

```json
{"camera_id":"CAMKRTVM00001","event":"motion_detected","timestamp":"2026-06-27T12:00:00Z"}
```

---

# 1. Update .env with Kong vars (from env_kong_additions.txt) + the secret above
# 2. Apply docker-compose.yml patches (Kong services + app service no longer exposing :8000)
# 3. Rebuild app with new deps (passlib)
docker compose build app frontend

# 4. Run the new migration
docker compose run --rm db_migrate

# 5. Bring up Postgres-dependent Kong bootstrap first
docker compose up -d kong-db-init
docker compose up -d kong-migration
docker compose up -d kong
# wait for kong healthy
docker compose up -d kong-config   # provisions routes/JWT/consumer — runs once
docker compose up -d konga

# 6. Create your first admin user directly in the DB (bootstrap — no UI exists yet for the very first user)
docker compose exec app python3 -c "
from app.services.auth_service import hash_password
print(hash_password('Shahid1234'))
"
docker compose exec postgres psql -U surv -d sarvanetra -c "
INSERT INTO survapp_user (username, password_hash, role, is_active)
VALUES ('admin', '\$2b\$12\$4PiYtdRs5gssEaluoV7Luedi3lhGbf5BCCSl9ZYZAYqHCZ8aVXAQa.', 'admin', true);
"
docker compose run -d --name tmp_migrate app sleep 60
docker cp app/alembic/versions/0002_add_users.py \
  tmp_migrate:/code/app/alembic/versions/0002_add_users.py
docker cp app/alembic/versions/0003_company_hierarchy.py \
  tmp_migrate:/code/app/alembic/versions/0003_company_hierarchy.py
docker cp app/alembic/versions/0004_bsnl_masters.py \
  tmp_migrate:/code/app/alembic/versions/0004_bsnl_masters.py
docker exec tmp_migrate alembic upgrade head
docker rm -f tmp_migrate

docker compose exec mediamtx sh -c 'rm -rf /recordings/*'
docker container prune -f
docker image prune -a -f
docker volume prune -f
docker builder prune -a -f
docker compose exec mediamtx df -h