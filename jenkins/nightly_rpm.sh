#!/bin/bash
DOCKER_SUFFIX=rpm
. ./jenkins/common/default_variables.sh

. ./jenkins/common/setup_docker.sh

. ./jenkins/common/set_max_map_count.sh

. ./jenkins/common/setup_selenium.sh
. ./jenkins/common/evaluate_force.sh
. ./jenkins/common/load_git_submodules.sh

# . ./jenkins/common/launch_minio.sh

. ./jenkins/common/register_cleanup_trap.sh

docker run \
       "${DOCKER_ARGS[@]}" \
       \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       \
       --privileged \
       -itd \
       \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

docker exec \
       "${DOCKER_NAME}" \
       /home/release-test-automation/release_tester/full_download_upgrade.py \
       --old-version "${OLD_VERSION}" \
       --new-version "${NEW_VERSION}" \
       --no-zip \
       "${RTA_ARGS[@]}" \
       "${@}"
result=$?

docker stop "${DOCKER_NAME}"

. ./jenkins/common/cleanup_ownership.sh
. ./jenkins/common/gather_coredumps.sh

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED ${DOCKER_SUFFIX}!"
    exit 1
fi
