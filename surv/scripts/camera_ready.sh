#!/bin/sh
# Hook for camera becoming ready

CAMERA="${MTX_PATH}"
TIMESTAMP=$(date +%s)

LOG_DIR="/recordings/logs"
mkdir -p "$LOG_DIR"
echo "[$(date)] Camera ready: $CAMERA" >> $LOG_DIR/kafka_status_hook.log

MESSAGE="{\"event_type\":\"camera_status\",\"camera\":\"$CAMERA\",\"status\":\"ready\",\"timestamp\":$TIMESTAMP}"

echo "$MESSAGE" | kcat -b "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}" \
  -t "${KAFKA_TOPIC_STATUS:-camera.status}" \
  -P > /dev/null 2>&1 

exit 0