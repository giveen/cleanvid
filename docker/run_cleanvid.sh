#!/usr/bin/env bash

set -euo pipefail

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

# Enable tab completion for video files
shopt -s nullglob
VIDEO_DIR="$(pwd)"
VIDEO_FILES=("$VIDEO_DIR"/*.mp4 "$VIDEO_DIR"/*.mkv "$VIDEO_DIR"/*.avi)

# Prompt user to select a video file
echo "🎬 Available video files:"
select VIDEO in "${VIDEO_FILES[@]}"; do
  [[ -n "$VIDEO" ]] && break
done

BASENAME="$(basename "$VIDEO")"
NAME="${BASENAME%.*}"
SRT="$VIDEO_DIR/$NAME.srt"

# Check for matching .srt file
if [[ -f "$SRT" ]]; then
  echo "📝 Found matching subtitle file: $SRT"
else
  echo "🔍 No matching .srt file found — attempting to download with subliminal..."
  $ENGINE run --rm \
    -v "$VIDEO_DIR:/data" \
    -w /data \
    "$IMAGE" subliminal download -l en "$BASENAME"
  if [[ -f "$SRT" ]]; then
    echo "✅ Subtitle downloaded: $SRT"
  else
    echo "❌ Failed to download subtitles. Exiting."
    exit 1
  fi
fi

# Run cleanvid with GPU acceleration
echo "🚀 Running cleanvid with GPU acceleration..."
$ENGINE run --rm --gpus all \
  -v "$VIDEO_DIR:/data" \
  -v /usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:/usr/lib/x86_64-linux-gnu/libnvidia-encode.so.1:ro \
  -v /usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:/usr/lib/x86_64-linux-gnu/libnvcuvid.so.1:ro \
  -w /data \
  "$IMAGE" \
  -i "$BASENAME" -s "$NAME.srt" --re-encode-video -o "${NAME}.clean.mp4"

echo "✅ Output created: ${NAME}.clean.mp4"
