#!/bin/bash

GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.10.0-nightly
fi
if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="$(pwd)/package_cache/"
fi

force_arg=()
if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
  force_arg=(--force)
fi

if test -n "$SOURCE"; then
    force_arg+=(--new-source "$SOURCE")
else
    force_arg+=(--remote-host "172.16.1.22")
fi

VERSION_TAR_NAME="${NEW_VERSION}_deb_version.tar"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir
mkdir -p allure-results

DOCKER_DEB_NAME=release-test-automation-deb

DOCKER_DEB_TAG="${DOCKER_DEB_NAME}:$(cat containers/this_version.txt)"

docker kill "${DOCKER_DEB_NAME}" || true
docker rm "${DOCKER_DEB_NAME}" || true

trap 'docker kill "${DOCKER_DEB_NAME}";
      docker rm "${DOCKER_DEB_NAME}"
     ' EXIT

DOCKER_NAMESPACE="arangodb/"
if docker pull "${DOCKER_NAMESPACE}${DOCKER_DEB_TAG}"; then
    echo "using ready built container"
else
    docker build containers/docker_deb -t "${DOCKER_DEB_TAG}" || exit
    DOCKER_NAMESPACE=""
fi

ssh -o StrictHostKeyChecking=no -T git@github.com
git clone git@github.com:arangodb/release-test-automation-helpers.git
mv $(pwd)/release-test-automation-helpers $(pwd)/release_tester/tools/external_helpers

docker run \
       --ulimit core=-1 \
       -v "$(pwd):/home/release-test-automation" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "${PACKAGE_CACHE}:/home/release-test-automation/package_cache" \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       --env="PYTHONUNBUFFERED=1" \
       --env="WORKSPACE=/home/release-test-automation/" \
       --env="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
       --env="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
       --env="AWS_REGION=$AWS_REGION" \
       --env="AWS_ACL=$AWS_ACL" \
       \
       --name="${DOCKER_DEB_NAME}" \
       --rm \
       --privileged \
       -itd \
       \
       "${DOCKER_NAMESPACE}${DOCKER_DEB_TAG}" \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

docker exec \
          "${DOCKER_DEB_NAME}" \
          /home/release-test-automation/release_tester/full_download_test.py \
          --new-version "${NEW_VERSION}" \
          --no-zip \
          --verbose \
          --alluredir /home/allure-results \
          --git-version "${GIT_VERSION}" \
          "${force_arg[@]}" \
          "${@}"
result=$?

docker stop "${DOCKER_TAR_NAME}"

# Cleanup ownership:
docker run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       --rm \
       "${DOCKER_DEB_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results

docker run \
       -v /tmp/tmp:/tmp/ \
       --rm \
       "${DOCKER_TAR_TAG}" \
       rm -f /tmp/config.yml 

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED DEB!"
    exit 1
fi