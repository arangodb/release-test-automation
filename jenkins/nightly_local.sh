#!/bin/bash
RTA_DIR="$(pwd)"
MODE=native
. "${RTA_DIR}/jenkins/common/detect_podman.sh"
. "${RTA_DIR}/jenkins/common/default_variables.sh"
. "${RTA_DIR}/jenkins/common/setup_docker.sh"
. "${RTA_DIR}/jenkins/common/set_max_map_count.sh"
. "${RTA_DIR}/jenkins/common/setup_selenium.sh"
. "${RTA_DIR}/jenkins/common/evaluate_force.sh"
. "${RTA_DIR}/jenkins/common/load_git_submodules.sh"
. "${RTA_DIR}/jenkins/common/launch_minio.sh"
. "${RTA_DIR}/jenkins/common/register_cleanup_trap.sh"

"${RTA_DIR}/release_tester/full_download_upgrade.py" \
       --old-version "${OLD_VERSION}" \
       --new-version "${NEW_VERSION}" \
       "${RTA_ARGS[@]}" \
       "${@}"
result=$?

. "${RTA_DIR}/jenkins/common/cleanup_ownership.sh"
. '${RTA_DIR}/jenkins/common/gather_coredumps.sh"

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED ${DOCKER_SUFFIX}!"
    exit 1
fi
