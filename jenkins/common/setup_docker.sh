DOCKER_NETWORK_NAME=rta-bridge
DOCKER_NAME="release-test-automation-${DOCKER_SUFFIX}"

DOCKER_TAG="${DOCKER_NAME}:$(cat containers/this_version.txt)${ARCH}"
DOCKER_NAMESPACE="arangodb/"
if docker pull "${DOCKER_NAMESPACE}${DOCKER_TAG}"; then
    echo "using ready built container"
else
    docker build "containers/docker_$(echo "${DOCKER_SUFFIX}"|sed "s;-;_;g")${ARCH}"  -t "${DOCKER_TAG}" || exit
    DOCKER_NAMESPACE=""
fi

. ./jenkins/common/pre_cleanup_docker.sh

docker network create $DOCKER_NETWORK_NAME
DOCKER_ARGS=(
    --env="BUILD_NUMBER=${BUILD_NUMBER}" \
         --env="PYTHONUNBUFFERED=1" \
         --env="RTA_LOCAL_HTTPUSER=${RTA_LOCAL_HTTPUSER}" \
         --env="WORKSPACE=/home/release-test-automation/" \
         --env="AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID" \
         --env="AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY" \
         --env="AWS_REGION=$AWS_REGION" \
         --env="AWS_ACL=$AWS_ACL" \
         --network="${DOCKER_NETWORK_NAME}" \
         --name="${DOCKER_NAME}" \
         --ulimit core=-1 \
         --rm \
         -v "$(pwd):/home/release-test-automation" \
         -v "$(pwd)/test_dir:/home/test_dir" \
         -v "/tmp:/tmp" \
         -v "${ALLURE_DIR}:/home/allure-results" \
         -v "${PACKAGE_CACHE}:/home/release-test-automation/package_cache" \
         -v /dev/shm:/dev/shm \
        )

TRAP_CLEANUP=(
    "docker kill ${DOCKER_NAME}"
    "docker rm ${DOCKER_NAME}"
    "${TRAP_CLEANUP[@]}"
)
