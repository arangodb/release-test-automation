#!/bin/bash

ARCH="-$(uname -m)"

if test "${ARCH}" == "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
docker build containers/docker_deb${ARCH} -t $DOCKER_DEB_TAG${ARCH} || exit
docker push $DOCKER_DEB_TAG${ARCH} || exit

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
docker build containers/docker_rpm${ARCH} -t $DOCKER_RPM_TAG${ARCH} || exit
docker push $DOCKER_RPM_TAG${ARCH} || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
docker build containers/docker_tar${ARCH} -t $DOCKER_TAR_TAG${ARCH} || exit
docker push $DOCKER_TAR_TAG${ARCH} || exit
