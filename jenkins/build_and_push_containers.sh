#!/bin/bash

ARCH="-$(uname -m)"

if test "${ARCH}" -eq "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
docker build containers/docker_deb -t $DOCKER_DEB_TAG${ARCH} || exit
docker push $DOCKER_DEB_TAG${ARCH} || exit

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
docker build containers/docker_rpm -t $DOCKER_RPM_TAG${ARCH} || exit
docker push $DOCKER_RPM_TAG${ARCH} || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
docker build containers/docker_tar -t $DOCKER_TAR_TAG${ARCH} || exit
docker push $DOCKER_TAR_TAG${ARCH} || exit


docker manifest create $DOCKER_DEB_TAG \
--amend $DOCKER_DEB_TAG-amd64 \
--amend $DOCKER_DEB_TAG-arm64v8
docker manifest push $DOCKER_DEB_TAG

docker manifest create $DOCKER_RPM_TAG \
--amend $DOCKER_RPM_TAG-amd64 \
--amend $DOCKER_RPM_TAG-arm64v8
docker manifest push $DOCKER_TAR_TAG

docker manifest create $DOCKER_TAR_TAG \
--amend $DOCKER_TAR_TAG-amd64 \
--amend $DOCKER_TAR_TAG-arm64v8
docker manifest push $DOCKER_TAR_TAG
