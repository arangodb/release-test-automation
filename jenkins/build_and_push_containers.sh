#!/bin/bash

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
docker build containers/docker_deb -t $DOCKER_DEB_TAG || exit
docker push $DOCKER_DEB_TAG || exit

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
docker build containers/docker_rpm -t $DOCKER_RPM_TAG || exit
docker push $DOCKER_RPM_TAG || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
docker build containers/docker_tar -t $DOCKER_TAR_TAG || exit
docker push $DOCKER_TAR_TAG || exit