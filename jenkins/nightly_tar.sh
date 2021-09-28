#!/bin/bash

VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.8-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.9-nightly
fi
if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="$(pwd)/package_cache/"
fi

if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg='--force'
fi

if test -n "$SOURCE"; then
    force_arg="${force_arg} --old-source $SOURCE --new-source $SOURCE"
else
    force_arg="${force_arg} --remote-host $(host nas02.arangodb.biz |sed "s;.* ;;")"
fi

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_tar_version"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p "${VERSION_TAR_NAME}"
mkdir -p test_dir
mkdir -p allure-results
tar -xvf ${VERSION_TAR_NAME}.tar || true

DOCKER_TAR_NAME=release-test-automation-tar

DOCKER_TAR_TAG="${DOCKER_TAR_NAME}:$(cat containers/this_version.txt)"

docker kill $DOCKER_TAR_NAME || true
docker rm $DOCKER_TAR_NAME || true

trap "docker kill /$DOCKER_TAR_NAME; \
     docker rm /$DOCKER_TAR_NAME; \
     " EXIT

version=$(git rev-parse --verify HEAD)
if docker pull arangodb/$DOCKER_TAR_TAG; then
    echo "using ready built container"
else
    docker build containers/docker_tar -t $DOCKER_TAR_TAG || exit
fi

# we need --init since our upgrade leans on zombies not happening:
docker run \
       --ulimit core=-1 \
       -v $(pwd):/home/release-test-automation \
       -v $(pwd)/test_dir:/home/test_dir \
       -v $(pwd)/allure-results:/home/allure-results \
       -v "${PACKAGE_CACHE}":/home/package_cache \
       -v $(pwd)/${VERSION_TAR_NAME}:/home/versions \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       \
       --name=$DOCKER_TAR_NAME \
       --pid=host \
       --rm \
       --ulimit core=-1 \
       --init \
       \
       $DOCKER_TAR_TAG \
       \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --old-version "${OLD_VERSION}" \
          --new-version "${NEW_VERSION}" \
          --zip \
          --verbose \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args no-sandbox \
          --alluredir /home/allure-results \
          --git-version $GIT_VERSION \
          $force_arg $@
result=$?

# don't need docker stop $DOCKER_TAR_NAME

# Cleanup ownership:
docker run \
       -v $(pwd)/test_dir:/home/test_dir \
       -v $(pwd)/allure-results:/home/allure-results \
       --rm \
       $DOCKER_TAR_TAG \
       chown -R $(id -u):$(id -g) /home/test_dir /home/allure-results

if test "$result" -eq "0"; then
    echo "OK"
    tar -cvf ${VERSION_TAR_NAME}.tar ${VERSION_TAR_NAME}
else
    echo "FAILED TAR!"
    exit 1
fi
