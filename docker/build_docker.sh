#!/usr/bin/env bash

IMAGE="${CLEANVID_IMAGE:-oci.guero.org/cleanvid:gpu}"
ENGINE="${CONTAINER_ENGINE:-docker}"

set -e
set -o pipefail
set -u

[[ "$(uname -s)" = 'Darwin' ]] && REALPATH=grealpath || REALPATH=realpath
[[ "$(uname -s)" = 'Darwin' ]] && DIRNAME=gdirname || DIRNAME=dirname
if ! (type "$REALPATH" && type "$DIRNAME" && type $ENGINE) > /dev/null; then
  echo "$(basename "${BASH_SOURCE[0]}") requires $ENGINE, $REALPATH and $DIRNAME"
  exit 1
fi

export SCRIPT_PATH="$($DIRNAME $($REALPATH -e "${BASH_SOURCE[0]}"))"

# Optional: Timestamp-based image tagging
TAG_SUFFIX=$(date +%Y%m%d-%H%M)
IMAGE_TAG="${IMAGE}-${TAG_SUFFIX}"

pushd "$SCRIPT_PATH"/.. >/dev/null 2>&1
$ENGINE build -f docker/Dockerfile -t "${IMAGE_TAG}" .
popd >/dev/null 2>&1

echo "Build complete: ${IMAGE_TAG}"
