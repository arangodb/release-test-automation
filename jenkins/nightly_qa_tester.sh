#!/bin/bash

TEST_VERSION=$1
shift
ALL_TESTCASES=$1
shift
TEST_SOURCE=$1
shift

ARGS=("${@}")

for testpair in ${ALL_TESTCASES//;/ }; do
    echo $testpair
    testset=(${testpair//:/ })
    old_version=${testset[0]}
    new_version=${testset[1]}
    if test "${old_version}" == "${TEST_VERSION}"; then
        ARGS+=('--old-version' ":${TEST_VERSION}" --old-source "${TEST_SOURCE}")
    else
        ARGS+=('--old-version' "${old_version}" --old-source "public")
    fi

    if test "${new_version}" == "${TEST_VERSION}"; then
        ARGS+=('--new-version' ":${TEST_VERSION}" --new-source "${TEST_SOURCE}")
    else
        ARGS+=('--new-version' "${new_version}" --new-source "public")
    fi

done

VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi

if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="$(pwd)/package_cache/"
fi

force_arg=()
if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg=(--force)
fi
# force_arg+=(--remote-host "$(host nas02.arangodb.biz |sed "s;.* ;;")")

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_tar_version.tar"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir
mkdir -p allure-results

DOCKER_TAR_NAME=release-test-automation-tar

DOCKER_TAR_TAG="${DOCKER_TAR_NAME}:$(cat containers/this_version.txt)"

docker kill "$DOCKER_TAR_NAME" || true
docker rm "$DOCKER_TAR_NAME" || true

trap 'docker kill "${DOCKER_TAR_NAME}";
      docker rm "${DOCKER_TAR_NAME}";
     ' EXIT

if docker pull "arangodb/${DOCKER_TAR_TAG}"; then
    echo "using ready built container"
else
    docker build containers/docker_tar -t "${DOCKER_TAR_TAG}" || exit
fi

# we need --init since our upgrade leans on zombies not happening:
docker run \
       --ulimit core=-1 \
       -v "$(pwd):/home/release-test-automation" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "${PACKAGE_CACHE}:/home/package_cache" \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       \
       --name="${DOCKER_TAR_NAME}" \
       --pid=host \
       --rm \
       --ulimit core=-1 \
       --init \
       \
       "arangodb/${DOCKER_TAR_TAG}" \
       \
          /home/release-test-automation/release_tester/full_download_upgrade.py \
          --version-state-tar "/home/release-test-automation/${VERSION_TAR_NAME}" \
          --zip \
          --verbose \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args no-sandbox \
          --alluredir /home/allure-results \
          --git-version "$GIT_VERSION" \
          "${force_arg[@]}" \
          "${ARGS[@]}"
result=$?

# don't need docker stop $DOCKER_TAR_NAME

# Cleanup ownership:
docker run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       --rm \
       "${DOCKER_TAR_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED TAR!"
    exit 1
fi
