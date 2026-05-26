#!/bin/bash -x
. ./jenkins/common/detect_podman.sh

BASE_URL=$(echo "${1}" |sed 's;/test-ubuntu;;')

DOCKER_TAR_OSKARNEW_TAG="${BASE_URL}/release-test-automation-tar-oskarnew:${2}"

$DOCKER manifest rm $DOCKER_TAR_OSKARNEW_TAG
$DOCKER manifest create $DOCKER_TAR_OSKARNEW_TAG \
--amend $DOCKER_TAR_OSKARNEW_TAG-amd64 \
--amend $DOCKER_TAR_OSKARNEW_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_TAR_OSKARNEW_TAG
