#!/bin/bash
. ./jenkins/common/detect_podman.sh

ARCH="-$(uname -m)"

if test "${ARCH}" == "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
$DOCKER build containers/docker_deb${ARCH} -t $DOCKER_DEB_TAG${ARCH} || exit
$DOCKER push $DOCKER_DEB_TAG${ARCH} || exit

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
$DOCKER build containers/docker_rpm${ARCH} -t $DOCKER_RPM_TAG${ARCH} || exit
$DOCKER push $DOCKER_RPM_TAG${ARCH} || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
$DOCKER build containers/docker_tar${ARCH} -t $DOCKER_TAR_TAG${ARCH} || exit
$DOCKER push $DOCKER_TAR_TAG${ARCH} || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar-oskar:$(cat containers/this_version.txt)
$DOCKER build containers/docker_tar_oskar${ARCH} -t $DOCKER_TAR_TAG${ARCH} || exit
$DOCKER push $DOCKER_TAR_TAG${ARCH} || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar-oskarnew:$(cat containers/this_version.txt)
$DOCKER build containers/docker_tar_oskarnew${ARCH} -t $DOCKER_TAR_TAG${ARCH} || exit
$DOCKER push $DOCKER_TAR_TAG${ARCH} || exit
