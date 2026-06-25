#!/bin/sh
# Fast hook to send segment data to Kafka

CAMERA="${MTX_PATH}"
FILE_PATH="${MTX_SEGMENT_PATH}"
SEGMENT_DURATION="${MTX_SEGMENT_DURATION}"
TIMESTAMP=$(date +%s)

# Log for debugging
LOG_DIR="/recordings/logs"
mkdir -p "$LOG_DIR"
echo "[$(date)] Camera: $CAMERA, File: $FILE_PATH, Duration: $SEGMENT_DURATION" >> $LOG_DIR/kafka_hook.log

# Build single-line JSON message
MESSAGE="{\"event_type\":\"segment_complete\",\"camera_path\":\"$CAMERA\",\"file_path\":\"$FILE_PATH\",\"segment_duration\":\"$SEGMENT_DURATION\",\"timestamp\":$TIMESTAMP}"

# Send to Kafka in background (fast, non-blocking)
echo "$MESSAGE" | kcat -b "${KAFKA_BOOTSTRAP_SERVERS:-kafka:9092}" \
  -t "${KAFKA_TOPIC_SEGMENTS:-recording.segments}" \
  -P > /dev/null 2>&1 

exit 0