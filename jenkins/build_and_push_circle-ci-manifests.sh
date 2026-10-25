#!/bin/bash -x
. ./jenkins/common/detect_podman.sh

BASE_URL=$(echo "${1}" |sed 's;/test-ubuntu;;')

DOCKER_TAR_OSKARNEW_TAG="${BASE_URL}/release-test-automation-tar-oskarnew:${2}"

# Per-arch tags built with BuildKit are OCI indexes (image + provenance attestation),
# which "docker manifest create" refuses; imagetools merges them into the multi-arch tag.
$DOCKER buildx imagetools create -t "${DOCKER_TAR_OSKARNEW_TAG}" \
  "${DOCKER_TAR_OSKARNEW_TAG}-amd64" "${DOCKER_TAR_OSKARNEW_TAG}-arm64v8" || exit 1
