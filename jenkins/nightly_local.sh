#!/bin/bash
ulimit -n 65535
export LANGUAGE='en_US@utf-8'
export LANG='en_US@utf-8'
export LC_CTYPE='en_US@utf-8'
echo "locales locales/default_environment_locale select en_US.UTF-8" | debconf-set-selections |true
echo "locales locales/locales_to_be_generated multiselect en_US.UTF-8 UTF-8" | debconf-set-selections |true
rm "/etc/locale.gen" |true
dpkg-reconfigure --frontend noninteractive locales |true
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

# . "${RTA_DIR}/jenkins/common/cleanup_ownership.sh"
chown -R jenkins "${RTA_DIR}"
. '${RTA_DIR}/jenkins/common/gather_coredumps.sh"

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED ${DOCKER_SUFFIX}!"
    exit 1
fi
