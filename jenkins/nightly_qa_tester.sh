#!/bin/bash
. ./jenkins/common/detect_podman.sh

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

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_tar_version.tar"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir
mkdir -p allure-results

DOCKER_TAR_NAME=release-test-automation-tar

DOCKER_TAR_TAG="${DOCKER_TAR_NAME}:$(cat containers/this_version.txt)"

$DOCKER kill "$DOCKER_TAR_NAME" || true
$DOCKER rm "$DOCKER_TAR_NAME" || true

trap '$DOCKER kill "${DOCKER_TAR_NAME}";
      $DOCKER rm "${DOCKER_TAR_NAME}";
     ' EXIT

if $DOCKER pull "arangodb/${DOCKER_TAR_TAG}"; then
    echo "using ready built container"
else
    $DOCKER build containers/docker_tar -t "${DOCKER_TAR_TAG}" || exit
fi

ssh -o StrictHostKeyChecking=no -T git@github.com
if test ! -d $(pwd)/release_tester/tools/external_helpers; then
  git clone git@github.com:arangodb/release-test-automation-helpers.git
  mv $(pwd)/release-test-automation-helpers $(pwd)/release_tester/tools/external_helpers
fi
git submodule init
git submodule update

echo "Maximum number of memory mappings per process is: `cat /proc/sys/vm/max_map_count`"
echo "Setting maximum number of memory mappings per process to: $((`nproc`*8*8000))"
sudo sysctl -w "vm.max_map_count=$((`nproc`*8*8000))"
echo "Maximum number of memory mappings per process is: `cat /proc/sys/vm/max_map_count`"

# we need --init since our upgrade leans on zombies not happening:
$DOCKER run \
       --ulimit core=-1 \
       -v "$(pwd):/home/release-test-automation" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "${PACKAGE_CACHE}:/home/package_cache" \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       --env="PYTHONUNBUFFERED=1" \
       --env="RTA_LOCAL_HTTPUSER=${RTA_LOCAL_HTTPUSER}" \
       --env="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
       --env="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
       --env="AWS_REGION=$AWS_REGION" \
       --env="AWS_ACL=$AWS_ACL" \
       \
       --name="${DOCKER_TAR_NAME}" \
       --pid=host \
       --rm \
       --ulimit core=-1 \
       --init \
       \
       "arangodb/${DOCKER_TAR_TAG}" \
       \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --zip \
          --verbose \
          --alluredir /home/allure-results \
          --git-version "$GIT_VERSION" \
          "${force_arg[@]}" \
          "${@}"
result=$?

# don't need docker stop $DOCKER_TAR_NAME

# Cleanup ownership:
$DOCKER run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       --rm \
       "${DOCKER_TAR_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results

if [ `ls -1 $(pwd)/test_dir/core* 2>/dev/null | wc -l ` -gt 0 ]; then
    7z a coredumps $(pwd)/test_dir/core*
    printf "\nCoredumps found after testrun:\n $(ls -l $(pwd)/test_dir/core*)\n" >> $(pwd)/test_dir/testfailures.txt
    rm -f $(pwd)/test_dir/core*
    mv coredumps.7z $(pwd)/test_dir/
    echo "FAILED BY COREDUMP FOUND!"
    exit 1
fi

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED TAR!"
    exit 1
fi
