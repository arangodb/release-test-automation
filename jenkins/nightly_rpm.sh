#!/bin/bash

VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD)
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi

if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.7.0-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.8.0-nightly
fi
if test -n "$PACKAGE_CACHE"; then
    PACKAGE_CACHE=$(pwd)/package_cache
fi

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_rpm_version"
mkdir -p ${VERSION_TAR_NAME}
tar -xvf ${VERSION_TAR_NAME}.tar || true

DOCKER_RPM_NAME=release-test-automation-rpm-$(cat VERSION.json)

DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat VERSION.json)

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi

docker kill $DOCKER_RPM_NAME || true
docker rm $DOCKER_RPM_NAME || true

trap "docker kill $DOCKER_RPM_NAME; \
     docker rm $DOCKER_RPM_NAME; \
     " EXIT

version=$(git rev-parse --verify HEAD)

docker build containers/docker_rpm -t $DOCKER_RPM_TAG || exit

docker run \
       --ulimit core=-1 \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v $(PWD):/home/release-test-automation \
       -v $(PWD)/test_dir:/home/test_dir \
       -v "$PACKAGE_CACHE":/home/package_cache \
       -v $(PWD)/${VERSION_TAR_NAME}:/home/versions \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       \
       --rm \
       --privileged \
       --name=$DOCKER_RPM_NAME \
       -itd \
       \
       $DOCKER_RPM_TAG \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec $DOCKER_RPM_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;") \
          --old-version "${OLD_VERSION}" \
          --new-version "${NEW_VERSION}" \
          --no-zip \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args disable-dev-shm-usage \
          --selenium-driver-args no-sandbox \
          --selenium-driver-args remote-debugging-port=9222 \
          --selenium-driver-args start-maximized \
          $force_arg $@; then
    echo "OK"
    tar -cvf ${VERSION_TAR_NAME}.tar ${VERSION_TAR_NAME}
else
    echo "FAILED RPM!"
    exit 1
fi
