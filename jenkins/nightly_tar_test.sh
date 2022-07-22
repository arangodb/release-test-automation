#!/bin/bash

VERSION=$(cat VERSION.json)
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
    force_arg+=(--remote-host 172.17.4.0)
fi

VERSION_TAR_NAME="${NEW_VERSION}_tar_version.tar"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir/miniodata/home/test_dir
rm -rf test_dir/miniodata/home/test_dir/*
mkdir -p allure-results

ssh -o StrictHostKeyChecking=no -T git@github.com
git clone git@github.com:arangodb/release-test-automation-helpers.git
mv $(pwd)/release-test-automation-helpers $(pwd)/release_tester/tools/external_helpers

DOCKER_TAR_NAME=release-test-automation-tar

DOCKER_TAR_TAG="${DOCKER_TAR_NAME}:$(cat containers/this_version.txt)"

docker kill "$DOCKER_TAR_NAME" || true
docker rm "$DOCKER_TAR_NAME" || true

trap 'docker kill "${DOCKER_TAR_NAME}";
      docker rm "${DOCKER_TAR_NAME}";
      docker kill minio1;
      docker rm minio1;
      docker network rm minio-bridge;
     ' EXIT

DOCKER_NAMESPACE="arangodb/"
if docker pull "${DOCKER_NAMESPACE}${DOCKER_TAR_TAG}"; then
    echo "using ready built container"
else
    docker build containers/docker_tar -t "${DOCKER_TAR_TAG}" || exit
    DOCKER_NAMESPACE=""
fi

docker network create -d bridge minio-bridge


docker run -d \
  -p 9000:9000 \
  -p 9001:9001 \
  --network=minio-bridge \
  --name minio1 \
  -v $(pwd)/test_dir/miniodata:/data \
  -e "MINIO_ROOT_USER=minio" \
  -e "MINIO_ROOT_PASSWORD=minio123" \
  quay.io/minio/minio server /data --console-address ":9001"


# we need --init since our upgrade leans on zombies not happening:
docker run \
       --ulimit core=-1 \
       -v "$(pwd):/home/release-test-automation" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "${PACKAGE_CACHE}:/home/release-test-automation/package_cache" \
       -v /tmp/tmp:/tmp/ \
       -v /dev/shm:/dev/shm \
       --env="BUILD_NUMBER=${BUILD_NUMBER}" \
       --env="PYTHONUNBUFFERED=1" \
       --env="RTA_LOCAL_HTTPUSER=${RTA_LOCAL_HTTPUSER}" \
       --env="WORKSPACE=/home/release-test-automation/" \
       --env="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
       --env="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
       --env="AWS_REGION=$AWS_REGION" \
       --env="AWS_ACL=$AWS_ACL" \
       \
       --network=minio-bridge \
       --name="${DOCKER_TAR_NAME}" \
       --pid=host \
       --rm \
       --ulimit core=-1 \
       --init \
       \
       "${DOCKER_NAMESPACE}${DOCKER_TAR_TAG}" \
       \
          /home/release-test-automation/release_tester/full_download_test.py \
          --new-version "${NEW_VERSION}" \
          --zip \
          --hb-mode s3bucket \
          --verbose \
          --alluredir /home/allure-results \
          --git-version "$GIT_VERSION" \
          "${force_arg[@]}" \
          "${@}"
result=$?

# don't need docker stop $DOCKER_TAR_NAME

# Cleanup ownership:
docker run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v $(pwd)/test_dir/miniodata:/data \
       --rm \
       "${DOCKER_TAR_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results /data/*

docker run \
       -v /tmp/tmp:/tmp/ \
       --rm \
       "${DOCKER_TAR_TAG}" \
       rm -f /tmp/config.yml 

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED TAR!"
    exit 1
fi
