#!/bin/sh


LOG_DIR="/recordings/logs"
LOG_FILE="$LOG_DIR/upload.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"
CAMERA_NAME="${MTX_PATH}"
FILE_PATH="${MTX_SEGMENT_PATH}"
TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
FILENAME="${CAMERA_NAME}_${TIMESTAMP}.mp4"

echo "[$(date)] Upload request: Path=$CAMERA_NAME, File=$FILE_PATH" >> $LOG_FILE

if [ ! -f "$FILE_PATH" ]; then
    echo "[$(date)] ERROR: File not found: $FILE_PATH" >> $LOG_FILE
    exit 1
fi

# Upload to MinIO via mc
mc alias set myminio http://minio:9000 minioadmin minioadmin123 > /dev/null 2>&1
mc mb myminio/recordings/$CAMERA_NAME --ignore-existing
if mc cp "$FILE_PATH" "myminio/recordings/$CAMERA_NAME/$FILENAME"; then
    echo "[$(date)] Uploaded: $FILENAME" >> $LOG_FILE
else
    echo "[$(date)] Upload failed: $FILENAME" >> $LOG_FILE
fi

