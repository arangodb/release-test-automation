#!/bin/bash -x
. ./jenkins/common/detect_podman.sh

DOCKER_TAR_OSKARNEW_TAG=arangodb/release-test-automation-tar-oskarnew:$1

$DOCKER manifest rm $DOCKER_TAR_OSKARNEW_TAG
$DOCKER manifest create $DOCKER_TAR_OSKARNEW_TAG \
--amend $DOCKER_TAR_OSKARNEW_TAG-amd64 \
--amend $DOCKER_TAR_OSKARNEW_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_TAR_OSKARNEW_TAG
