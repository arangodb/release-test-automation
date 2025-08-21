#!/bin/bash -x
. ./jenkins/common/detect_podman.sh

ARCH="-$(uname -m)"

if test "${ARCH}" == "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

DOCKER_TAR_TAG=${1}arangodb/release-test-automation-tar-oskarnew:$2
$DOCKER build containers/docker_tar_oskarnew${ARCH} -t $DOCKER_TAR_TAG${ARCH} || exit
$DOCKER push $DOCKER_TAR_TAG${ARCH} || exit
