#!/usr/bin/env bash

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

set -e
set -o pipefail
set -u

ENCODING="utf-8"

[[ "$(uname -s)" = 'Darwin' ]] && REALPATH=grealpath || REALPATH=realpath
[[ "$(uname -s)" = 'Darwin' ]] && DIRNAME=gdirname || DIRNAME=dirname
if ! (type "$REALPATH" && type "$DIRNAME" && type $ENGINE) > /dev/null; then
  echo "$(basename "${BASH_SOURCE[0]}") requires $ENGINE, $REALPATH and $DIRNAME"
  exit 1
fi

export SCRIPT_PATH="$($DIRNAME $($REALPATH -e "${BASH_SOURCE[0]}"))"

# Check for required NVIDIA runtime libraries
REQUIRED_LIBS=("libnvidia-encode.so.1" "libnvcuvid.so.1")
for lib in "${REQUIRED_LIBS[@]}"; do
  if [[ ! -f "$SCRIPT_PATH/../docker/$lib" ]]; then
    echo "❌ Missing required runtime library: $lib"
    echo "➡️  Copy it from your host system into docker/ before building."
    exit 1
  fi
done

# Optional: Timestamp-based image tagging
TAG_SUFFIX=$(date +%Y%m%d-%H%M)
IMAGE_TAG="${IMAGE}-${TAG_SUFFIX}"

pushd "$SCRIPT_PATH"/.. >/dev/null 2>&1
$ENGINE build -f docker/Dockerfile -t "${IMAGE_TAG}" .
popd >/dev/null 2>&1

echo "Build complete: ${IMAGE_TAG}"
