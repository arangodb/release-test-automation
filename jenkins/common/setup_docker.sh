if test -z "$DOCKER_NETWORK_NAME"; then
    DOCKER_NETWORK_NAME=rta-bridge
fi

if test -z "${DOCKER_CONTAINER}"; then
    DOCKER_NAME="release-test-automation-${DOCKER_SUFFIX}"

    DOCKER_TAG="${DOCKER_NAME}:$(cat containers/this_version.txt)${ARCH}"
    DOCKER_NAMESPACE="arangodb/"
    if test "${MODE}" != "native"; then
        if ${DOCKER} pull "${REGISTRY_URL}${DOCKER_NAMESPACE}${DOCKER_TAG}"; then
            echo "using ready built container"
        else
            ${DOCKER} build "containers/${DOCKER}_$(echo "${DOCKER_SUFFIX}"|sed "s;-;_;g")${ARCH}"  -t "${DOCKER_TAG}" || exit
            DOCKER_NAMESPACE=""
        fi
    fi
fi
. ./jenkins/common/pre_cleanup_docker.sh

if test "$DOCKER_NETWORK_NAME" != "host"; then
    ${DOCKER} network create $DOCKER_NETWORK_NAME
fi
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
# containerd         --rm \
         -v "$(pwd):/home/release-test-automation" \
         -v "$(pwd)/test_dir:/home/test_dir" \
         -v "/tmp:/tmp" \
         -v "${ALLURE_DIR}:/home/allure-results" \
         -v "${PACKAGE_CACHE}:/home/release-test-automation/package_cache" \
         -v /dev/shm:/dev/shm \
        )

TRAP_CLEANUP=()
if test "${MODE}" != "native"; then
    TRAP_CLEANUP+=(
        "${DOCKER} kill ${DOCKER_NAME}"
    )
fi
TRAP_CLEANUP+=(
    "${DOCKER} rm ${DOCKER_NAME}"
    "${TRAP_CLEANUP[@]}"
)
