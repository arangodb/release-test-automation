#!/bin/bash
. ./jenkins/common/detect_podman.sh

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat containers/this_version.txt)
DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat containers/this_version.txt)
DOCKER_TAR_TAG=arangodb/release-test-automation-tar:$(cat containers/this_version.txt)
DOCKER_TAR_OSKAR_TAG=arangodb/release-test-automation-tar-oskar:$(cat containers/this_version.txt)
DOCKER_TAR_OSKARNEW_TAG=arangodb/release-test-automation-tar-oskarnew:$(cat containers/this_version.txt)

$DOCKER manifest rm $DOCKER_DEB_TAG
$DOCKER manifest create $DOCKER_DEB_TAG \
--amend $DOCKER_DEB_TAG-amd64 \
--amend $DOCKER_DEB_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_DEB_TAG

$DOCKER manifest rm $DOCKER_RPM_TAG
$DOCKER manifest create $DOCKER_RPM_TAG \
--amend $DOCKER_RPM_TAG-amd64 \
--amend $DOCKER_RPM_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_RPM_TAG

$DOCKER manifest rm $DOCKER_TAR_TAG
$DOCKER manifest create $DOCKER_TAR_TAG \
--amend $DOCKER_TAR_TAG-amd64 \
--amend $DOCKER_TAR_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_TAR_TAG


$DOCKER manifest rm $DOCKER_TAR_OSKAR_TAG
$DOCKER manifest create $DOCKER_TAR_OSKAR_TAG \
--amend $DOCKER_TAR_OSKAR_TAG-amd64 \
--amend $DOCKER_TAR_OSKAR_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_TAR_OSKAR_TAG

$DOCKER manifest rm $DOCKER_TAR_OSKARNEW_TAG
$DOCKER manifest create $DOCKER_TAR_OSKARNEW_TAG \
--amend $DOCKER_TAR_OSKARNEW_TAG-amd64 \
--amend $DOCKER_TAR_OSKARNEW_TAG-arm64v8
$DOCKER manifest push --purge $DOCKER_TAR_OSKARNEW_TAG
