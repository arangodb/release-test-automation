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

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_deb_version"
mkdir -p ${VERSION_TAR_NAME}
tar -xvf ${VERSION_TAR_NAME}.tar || true

DOCKER_DEB_NAME=release-test-automation-deb-$(cat VERSION.json)

DOCKER_DEB_TAG=arangodb/release-test-automation-deb:$(cat VERSION.json)

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi

docker kill $DOCKER_DEB_NAME || true
docker rm $DOCKER_DEB_NAME || true

trap "docker kill $DOCKER_DEB_NAME; \
     docker rm $DOCKER_DEB_NAME \
     " EXIT

version=$(git rev-parse --verify HEAD)

docker build containers/docker_deb -t $DOCKER_DEB_TAG || exit

docker run -itd \
       --ulimit core=-1 \
       --privileged \
       --name=$DOCKER_DEB_NAME \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v $(pwd):/home/release-test-automation \
       -v $(pwd)/test_dir:/home/test_dir \
       -v "$PACKAGE_CACHE":/home/package_cache \
       -v $(pwd)/${VERSION_TAR_NAME}:/home/versions \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       --pid=host \
        --rm \
       \
       $DOCKER_DEB_TAG \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec $DOCKER_DEB_NAME \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --old-version "${OLD_VERSION}" \
          --new-version "${NEW_VERSION}" \
          --verbose \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args no-sandbox \
          --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;") \
          --no-zip $force_arg $@; then
    echo "OK"
    tar -cvf ${VERSION_TAR_NAME}.tar ${VERSION_TAR_NAME}
else
    echo "FAILED DEB!"
    exit 1
fi
