#!/usr/bin/env bash
# edge-sim/generate_clips.sh
# Generate sample clips for edge NVR simulation.
# Output: edge-sim/clips/site-01.mp4, site-02.mp4, site-03.mp4
#
# Run once. Each ffmpeg camera process at runtime does -c copy (no re-encode).
# Requires: ffmpeg with libx264 + fontconfig

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLIPS_DIR="$SCRIPT_DIR/clips"
mkdir -p "$CLIPS_DIR"

DURATION=60          # seconds — long enough for looping
WIDTH=640
HEIGHT=480
FPS=15
BITRATE=400k

for i in 1 2 3; do
  SITE_NUM=$(printf "%02d" $i)
  SITE_LABEL="SITE-${SITE_NUM}"
  OUTPUT="$CLIPS_DIR/site-${SITE_NUM}.mp4"

  if [[ -f "$OUTPUT" ]]; then
    echo "[skip] $OUTPUT already exists"
    continue
  fi

  echo "[gen] Creating $OUTPUT (${DURATION}s, ${WIDTH}x${HEIGHT}, ${BITRATE})..."

  # Different background hue per site for easy visual distinction:
  # Site 01 = cool blue-grey, Site 02 = warm amber, Site 03 = teal
  case $i in
    1) HUE="hue=h=210" ; BG="color=c=0x1a2a3a" ;;
    2) HUE="hue=h=30"  ; BG="color=c=0x3a2a0a" ;;
    3) HUE="hue=h=175" ; BG="color=c=0x0a2a2a" ;;
  esac

  ffmpeg -y \
    -f lavfi -i "testsrc2=size=${WIDTH}x${HEIGHT}:rate=${FPS},${HUE}" \
    -vf "drawtext=\
fontcolor=white:\
fontsize=36:\
box=1:boxcolor=black@0.6:boxborderw=8:\
text='${SITE_LABEL}':\
x=(w-text_w)/2:y=30,\
drawtext=\
fontcolor=yellow:\
fontsize=20:\
box=1:boxcolor=black@0.5:boxborderw=4:\
text='Simulated NVR Camera':\
x=(w-text_w)/2:y=h-50" \
    -t $DURATION \
    -c:v libx264 \
    -preset fast \
    -b:v $BITRATE \
    -pix_fmt yuv420p \
    -an \
    -movflags +faststart \
    "$OUTPUT"

  echo "[ok]  $OUTPUT generated ($(du -sh "$OUTPUT" | cut -f1))"
done

echo ""
echo "All clips ready in $CLIPS_DIR:"
ls -lh "$CLIPS_DIR"
