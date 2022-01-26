#!/bin/bash

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
docker pull $DOCKER_DEB_TAG || exit

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
docker pull $DOCKER_RPM_TAG || exit

DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
docker pull $DOCKER_TAR_TAG || exit
