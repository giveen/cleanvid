#!/usr/bin/env bash

set -euo pipefail

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

# Enable tab completion for video files
shopt -s nullglob
VIDEO_DIR="$(pwd)"
VIDEO_FILES=("$VIDEO_DIR"/*.mp4 "$VIDEO_DIR"/*.mkv "$VIDEO_DIR"/*.avi)

if [[ ${#VIDEO_FILES[@]} -eq 0 ]]; then
    echo "❌ No video files found in $(pwd). Exiting."
    exit 1
fi

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

# Check for GPU availability and run with appropriate flags
if $ENGINE run --rm --gpus all -it "$IMAGE" /usr/local/bin/cleanvid --help >/dev/null 2>&1; then
  # Test actual FFmpeg hardware acceleration capability
  if $ENGINE run --rm --gpus all "$IMAGE" /usr/local/bin/ffmpeg -hwaccel cuda -f lavfi -i nullsrc=s=1280x720 -t 1 -c:v h264_nvenc -y /dev/null >/dev/null 2>&1; then
    echo "🚀 Running cleanvid with GPU acceleration..."
    $ENGINE run --rm --gpus all \
      -v "$VIDEO_DIR:/data" \
      -w /data \
      "$IMAGE" \
      -i "$BASENAME" -s "$NAME.srt" --re-encode-video -o "${NAME}.clean.mp4"
  else
    echo "⚠️  CUDA not available — running with CPU encoding..."
    $ENGINE run --rm \
      -v "$VIDEO_DIR:/data" \
      -w /data \
      "$IMAGE" \
      -i "$BASENAME" -s "$NAME.srt" --re-encode-video -o "${NAME}.clean.mp4"
  fi
else
  echo "⚠️  CUDA not available — running with CPU encoding..."
  $ENGINE run --rm \
    -v "$VIDEO_DIR:/data" \
    -w /data \
    "$IMAGE" \
    -i "$BASENAME" -s "$NAME.srt" --re-encode-video -o "${NAME}.clean.mp4"
fi

echo "✅ Output created: ${NAME}.clean.mp4"
