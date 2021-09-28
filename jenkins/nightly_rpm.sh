#!/bin/bash

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

force_arg=()
if test -n "$FORCE" -o "$TEST_BRANCH" != 'master'; then
  force_arg=(--force)
fi

if test -n "$SOURCE"; then
    force_arg+=(--old-source "$SOURCE" --new-source "$SOURCE")
else
    force_arg+=(--remote-host "$(host nas02.arangodb.biz |sed "s;.* ;;")")
fi

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_rpm_version"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p "${VERSION_TAR_NAME}"
mkdir -p test_dir
mkdir -p allure-results
tar -xvf ${VERSION_TAR_NAME}.tar || true

DOCKER_RPM_NAME=release-test-automation-rpm

DOCKER_RPM_TAG="${DOCKER_RPM_NAME}:$(cat containers/this_version.txt)"

docker kill "${DOCKER_RPM_NAME}" || true
docker rm "${DOCKER_RPM_NAME}" || true

trap 'docker kill "${DOCKER_RPM_NAME}";
      docker rm "${DOCKER_RPM_NAME}";
     ' EXIT

if docker pull "arangodb/${DOCKER_RPM_TAG}"; then
    echo "using ready built container"
else
    docker build containers/docker_rpm -t "${DOCKER_RPM_TAG}" || exit
fi

docker run \
       --ulimit core=-1 \
       -v "$(pwd):/home/release-test-automation" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "${PACKAGE_CACHE}:/home/package_cache" \
       -v "$(pwd)/${VERSION_TAR_NAME}:/home/versions" \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       \
       --name="${DOCKER_RPM_NAME}" \
       --rm \
       --privileged \
       -itd \
       \
       "${DOCKER_RPM_TAG}" \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

docker exec \
          "${DOCKER_RPM_NAME}" \
          /home/release-test-automation/release_tester/full_download_upgrade_test.py \
          --old-version "${OLD_VERSION}" \
          --new-version "${NEW_VERSION}" \
          --no-zip \
          --verbose \
          --selenium Chrome \
          --selenium-driver-args headless \
          --selenium-driver-args disable-dev-shm-usage \
          --selenium-driver-args no-sandbox \
          --selenium-driver-args remote-debugging-port=9222 \
          --selenium-driver-args start-maximized \
          --alluredir /home/allure-results \
          --git-version "${GIT_VERSION}" \
          "${force_arg[@]}" \
          "${@}"
result=$?

docker stop "${DOCKER_RPM_NAME}"

# Cleanup ownership:
docker run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       --rm \
       "${DOCKER_RPM_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results

if test "${result}" -eq "0"; then
    echo "OK"
    tar -cvf "${VERSION_TAR_NAME}.tar" "${VERSION_TAR_NAME}"
else
    echo "FAILED RPM!"
    exit 1
fi
