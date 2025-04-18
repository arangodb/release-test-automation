#!/bin/bash
. ./jenkins/common/detect_podman.sh

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

if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
  force_arg='--force'
fi
if test -n "$SOURCE"; then
    force_arg+=(--new-source "$SOURCE")
else
    force_arg+=(--remote-host 172.17.4.0)
fi

trap "$DOCKER kill $DOCKER_DEB_NAME; \
     $DOCKER rm $DOCKER_DEB_NAME; \
     $DOCKER kill $DOCKER_RPM_NAME; \
     $DOCKER rm $DOCKER_RPM_NAME;" EXIT

version=$(git rev-parse --verify HEAD)

$DOCKER build containers/docker_deb -t $DOCKER_DEB_TAG || exit
$DOCKER build containers/docker_rpm -t $DOCKER_RPM_TAG || exit

ssh -o StrictHostKeyChecking=no -T git@github.com
if test ! -d $(pwd)/release_tester/tools/external_helpers; then
  git clone git@github.com:arangodb/release-test-automation-helpers.git
  mv $(pwd)/release-test-automation-helpers $(pwd)/release_tester/tools/external_helpers
fi
git submodule init
git submodule update

$DOCKER run -itd \
       --ulimit core=-1 \
       --privileged \
       --name=$DOCKER_DEB_NAME \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v `pwd`:/home/release-test-automation \
       -v `pwd`/package_cache/:/home/package_cache \
       -v /tmp:/home/test_dir \
       -v $(pwd)/allure-results:/home/allure-results \
       -v /tmp/tmp:/tmp/ \
       -v /tmp/deb_versions:/home/versions \
       \
       $DOCKER_DEB_TAG \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if $DOCKER exec $DOCKER_DEB_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --selenium Chrome \
          --selenium-driver-args headless \
          --no-zip $force_arg $@; then
    echo "OK"
else
    echo "FAILED DEB!"
    exit 1
fi


$DOCKER run \
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

if $DOCKER exec $DOCKER_RPM_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --no-zip \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args disable-dev-shm-usage \
          --selenium-driver-args no-sandbox \
          --selenium-driver-args remote-debugging-port=9222 \
          --selenium-driver-args start-maximized \
          --alluredir /home/allure-results \
          $force_arg $@; then
    echo "OK"
else
    echo "FAILED RPM!"
    exit 1
fi
