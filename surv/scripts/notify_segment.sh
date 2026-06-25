#!/bin/sh

CAMERA="${MTX_PATH}"
FILE_PATH="${MTX_SEGMENT_PATH}"

echo "Camera: $CAMERA"
echo "File: $FILE_PATH"

python3 /app/upload_to_minio.py "$FILE_PATH"