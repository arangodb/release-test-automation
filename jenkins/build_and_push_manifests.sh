#!/bin/bash

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)

docker manifest rm $DOCKER_DEB_TAG
docker manifest create $DOCKER_DEB_TAG \
--amend $DOCKER_DEB_TAG-amd64 \
--amend $DOCKER_DEB_TAG-arm64v8
docker manifest push --purge $DOCKER_DEB_TAG

docker manifest rm $DOCKER_RPM_TAG
docker manifest create $DOCKER_RPM_TAG \
--amend $DOCKER_RPM_TAG-amd64 \
--amend $DOCKER_RPM_TAG-arm64v8
docker manifest push --purge $DOCKER_RPM_TAG

docker manifest rm $DOCKER_TAR_TAG
docker manifest create $DOCKER_TAR_TAG \
--amend $DOCKER_TAR_TAG-amd64 \
--amend $DOCKER_TAR_TAG-arm64v8
docker manifest push --purge $DOCKER_TAR_TAG
