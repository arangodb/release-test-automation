#!/bin/bash
DOCKER_SUFFIX=tar
. ./jenkins/common/default_variables.sh

. ./jenkins/common/setup_docker.sh


. ./jenkins/common/set_max_map_count.sh

. ./jenkins/common/setup_selenium.sh
. ./jenkins/common/evaluate_force.sh
. ./jenkins/common/load_git_submodules.sh

. ./jenkins/common/launch_minio.sh

. ./jenkins/common/register_cleanup_trap.sh

# we need --init since our upgrade leans on zombies not happening:
docker run \
       "${DOCKER_ARGS[@]}" \
       \
       --pid=host \
       --rm \
       --init \
       \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       \
       /home/release-test-automation/release_tester/full_download_test.py \
       --new-version "${NEW_VERSION}" \
       --zip \
       \
       "${RTA_ARGS[@]}" \
       "${@}"
result=$?

# don't need docker stop $DOCKER_TAR_NAME

. ./jenkins/common/cleanup_ownership.sh
. ./jenkins/common/gather_coredumps.sh

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED ${DOCKER_SUFFIX}!"
    exit 1
fi
