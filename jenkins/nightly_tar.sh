#!/bin/bash

if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.7.0-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.8.0-nightly
fi
if test -n "$PACKAGE_CACHE"; then
    PACKAGE_CACHE=$(pwd)/package_cache
fi

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_tar_version"
mkdir -p package_cache
mkdir -p ${VERSION_TAR_NAME}
mkdir -p test_dir
tar -xvf ${VERSION_TAR_NAME}.tar || true

VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
DOCKER_TAG=arangodb/release-test-automation-tar
docker pull $DOCKER_TAG
DOCKER_NAME=release-test-automation-tar-${VERSION}
DOCKER_TAG=${DOCKER_TAG}:${VERSION}

docker rm -f $DOCKER_NAME

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi

trap "docker kill /$DOCKER_NAME; docker rm /$DOCKER_NAME;" EXIT
docker build containers/docker_tar -t $DOCKER_TAG
# we need --init since our upgrade leans on zombies not happening:
docker \
    run \
  --name=$DOCKER_NAME \
  -v /dev/shm:/dev/shm \
  -v $(pwd):/home/release-test-automation \
  -v $(pwd)/test_dir:/home/test_dir \
  -v "$PACKAGE_CACHE":/home/package_cache \
  -v $(pwd)/${VERSION_TAR_NAME}:/home/versions \
  --pid=host \
  --rm \
  --ulimit core=-1 \
  --init \
  $DOCKER_TAG \
  /home/release-test-automation/release_tester/full_download_upgrade_test.py \
      --zip \
      --verbose \
      --old-version $OLD_VERSION \
      --new-version $NEW_VERSION \
      --selenium Chrome \
      --selenium-driver-args headless \
      --selenium-driver-args no-sandbox \
      --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;") \
      $force_arg --git-version $GIT_VERSION $@
result=$?

# Cleanup ownership:
docker run \
       -v $(pwd)/test_dir:/home/test_dir \
       --rm \
       $DOCKER_TAG chown -R $(id -u):$(id -g) /home/test_dir

if test "$result" -eq "0"; then
    echo "OK"
    tar -cvf ${VERSION_TAR_NAME}.tar ${VERSION_TAR_NAME}
else
    echo "FAILED TAR!"
    exit 1
fi
