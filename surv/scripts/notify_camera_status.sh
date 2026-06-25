#!/bin/bash
# Fast hook for camera status changes

CAMERA="$1"
STATUS="$2"  # 'ready' or 'notReady'
TIMESTAMP=$(date +%s)

MESSAGE=$(cat <<EOF
{
  "event_type": "camera_status",
  "camera": "$CAMERA",
  "status": "$STATUS",
  "timestamp": $TIMESTAMP
}
EOF
)

echo "$MESSAGE" | kcat -b "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}" \
  -t "${KAFKA_TOPIC_STATUS:-camera.status}" \
  -P > /dev/null 2>&1 &

exit 0