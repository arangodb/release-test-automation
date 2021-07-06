#!/bin/bash

mkdir -p /tmp/rpm_versions /tmp/deb_versions
VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD)
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
DOCKER_DEB_NAME=release-test-automation-deb-$(cat VERSION.json)
DOCKER_RPM_NAME=release-test-automation-rpm-$(cat VERSION.json)

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat VERSION.json)
DOCKER_RPM_TAG=arangodb/release-test-automation-rpm:$(cat VERSION.json)

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi


trap "docker kill $DOCKER_DEB_NAME; \
     docker rm $DOCKER_DEB_NAME; \
     docker kill $DOCKER_RPM_NAME; \
     docker rm $DOCKER_RPM_NAME;" EXIT

version=$(git rev-parse --verify HEAD)

docker build containers/docker_deb -t $DOCKER_DEB_TAG || exit
docker build containers/docker_rpm -t $DOCKER_RPM_TAG || exit

docker run -itd \
       --ulimit core=-1 \
       --privileged \
       --name=$DOCKER_DEB_NAME \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v `pwd`:/home/release-test-automation \
       -v `pwd`/package_cache/:/home/package_cache \
       -v /tmp:/home/test_dir \
       -v /tmp/tmp:/tmp/ \
       -v /tmp/deb_versions:/home/versions \
       \
       $DOCKER_DEB_TAG \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec $DOCKER_DEB_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --selenium Chrome \
          --selenium-driver-args headless \
          --no-zip $force_arg $@; then
    echo "OK"
else
    echo "FAILED DEB!"
    exit 1
fi


docker run \
       --ulimit core=-1 \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v `pwd`:/home/release-test-automation \
       -v `pwd`/package_cache/:/home/package_cache \
       -v /tmp:/home/test_dir \
       -v /tmp/tmp:/tmp/ \
       -v /tmp/rpm_versions:/home/versions \
       \
       --privileged \
       --name=$DOCKER_RPM_NAME \
       -itd \
       \
       $DOCKER_RPM_TAG \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec $DOCKER_RPM_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --no-zip \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args disable-dev-shm-usage \
          --selenium-driver-args no-sandbox \
          --selenium-driver-args remote-debugging-port=9222 \
          --selenium-driver-args start-maximized \
          $force_arg $@; then
    echo "OK"
else
    echo "FAILED RPM!"
    exit 1
fi
