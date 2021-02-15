#!/bin/bash

if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.7.0-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.8.0-nightly
fi
mkdir -p package_cache
mkdir -p versions
mkdir -p test_dir
VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD)
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
DOCKER_NAME=release-test-automation-tar-${VERSION}
DOCKER_TAG=release-test-automation-tar:${VERSION}

tar -xvf versions.tar || true

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi


trap "docker kill /$DOCKER_NAME; docker rm /$DOCKER_NAME;" EXIT
docker build docker_tar -t $DOCKER_TAG
docker \
    run \
  --name=$DOCKER_NAME \
  -v `pwd`:/home/release-test-automation \
  -v `pwd`/test_dir:/home/test_dir \
  -v `pwd`/package_cache:/home/package_cache \
  -v `pwd`/versions:/home/versions \
  $DOCKER_TAG \
    /home/release-test-automation/release_tester/full_download_upgrade_test.py \
      --old-version $OLD_VERSION \
      --new-version $NEW_VERSION \
      --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;") \
      $force_arg --git-version $GIT_VERSION $@

tar -cvf versions.tar versions
