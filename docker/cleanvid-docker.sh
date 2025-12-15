#!/usr/bin/env bash

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

set -e
set -o pipefail
set -u

# Check for GPU availability and CUDA support
if ! $ENGINE run --rm --gpus all --entrypoint ffmpeg "$IMAGE" -hwaccel cuda -hide_banner -loglevel error -f lavfi -i nullsrc=s=1280x720 -t 1 -y /dev/null 2>/dev/null; then
  echo "CUDA not available — falling back to CPU encoding"
  GPU_ARGS=()
else
  echo "CUDA available — using GPU acceleration"
  GPU_ARGS=(--gpus all)
fi

# Run cleanvid with working directory and bind mount
$ENGINE run --rm "${GPU_ARGS[@]}" \
  -v "$(pwd)":/data \
  -w /data \
  "$IMAGE" "$@"
