#!/bin/bash
. ./jenkins/common/detect_podman.sh

VERSION=$(cat containers/this_version.txt)

# The per-architecture tags that build_and_push_containers.sh pushes are OCI image
# indexes when built with BuildKit (image + provenance attestation), and
# "docker manifest create" refuses those ("... is a manifest list").
# "buildx imagetools create" merges indexes and plain manifests alike into the
# multi-arch tag, so it works for both the old and the new per-arch tags.
for NAME in deb rpm tar tar-oskar tar-oskarnew; do
  TAG=arangodb/release-test-automation-${NAME}:${VERSION}
  echo "=== ${TAG}"
  $DOCKER buildx imagetools create -t "${TAG}" "${TAG}-amd64" "${TAG}-arm64v8" || exit 1
  $DOCKER buildx imagetools inspect "${TAG}" | grep -E "^Name:|Platform:" || exit 1
done
