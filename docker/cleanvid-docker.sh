#!/usr/bin/env bash

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

set -e
set -o pipefail
set -u

# Check for GPU availability
if ! $ENGINE run --rm --gpus all --entrypoint ffmpeg "$IMAGE" -encoders | grep -q h264_nvenc; then
  echo "NVENC not available — falling back to CPU encoding"
  GPU_ARGS=()
else
  echo "NVENC available — using GPU acceleration"
  GPU_ARGS=(--gpus all)
fi

# Run cleanvid with working directory and bind mount
$ENGINE run --rm "${GPU_ARGS[@]}" \
  -v "$(pwd)":/data \
  -w /data \
  "$IMAGE" "$@"
