#!/bin/bash
DOCKER_SUFFIX=tar-oskar

ALLURE_DIR="$(pwd)/allure-results"
if test -n "$WORKSPACE"; then
    ALLURE_DIR="${WORKSPACE}/allure-results"
fi
if test ! -d "${ALLURE_DIR}"; then 
    mkdir -p "${ALLURE_DIR}"
fi

cat /proc/sys/kernel/core_pattern
ARCH="-$(uname -m)"

if test "${ARCH}" == "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

VERSION=$(cat VERSION.json)
git status
GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.11.0-nightly
fi
 if test -z "$NEW_VERSION"; then
     NEW_VERSION="$(sed -e "s;-devel;;" "$(pwd)/../ArangoDB/ARANGO-VERSION")-src"
 fi
if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="$(pwd)/package_cache/"
fi

RTA_ARGS=()
if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
  RTA_ARGS+=(--force)
fi

if test -z "$UPGRADE_MATRIX"; then
    UPGRADE_MATRIX="${OLD_VERSION}:${NEW_VERSION}"
fi

if test -n "$SOURCE"; then
    RTA_ARGS+=(--other-source "$SOURCE")
else
    RTA_ARGS+=(--remote-host 172.17.4.0)
fi
if test "RUN_TEST"; then
    RTA_ARGS+=(--run-test)
else    
    RTA_ARGS+=(--no-run-test)
fi
if test "RUN_UPGRADE"; then
    RTA_ARGS+=(--run-upgrade)
else    
    RTA_ARGS+=(--no-run-upgrade)
fi
if test -z "${RTA_EDITION}"; then
    RTA_EDITION='C'
fi
IFS=',' read -r -a EDITION_ARR <<< "${RTA_EDITION}"
for one_edition in "${EDITION_ARR[@]}"; do
    RTA_ARGS+=(--edition "${one_edition}")
done

. ./jenkins/common/setup_docker.sh

. ./jenkins/common/set_max_map_count.sh

. ./jenkins/common/setup_selenium.sh
# . ./jenkins/common/evaluate_force.sh
. ./jenkins/common/load_git_submodules.sh

. ./jenkins/common/launch_minio.sh

. ./jenkins/common/register_cleanup_trap.sh

DOCKER_ARGS+=(
       -v "$(pwd)/../:/work"
       --env=WORK_DIR=/work/ArangoDB
)
# we need --init since our upgrade leans on zombies not happening:
docker run \
       "${DOCKER_ARGS[@]}" \
       --env="ASAN_OPTIONS=${ASAN_OPTIONS}" \
       --env="LSAN_OPTIONS=${LSAN_OPTIONS}" \
       --env="UBSAN_OPTIONS=${UBSAN_OPTIONS}" \
       --env="TSAN_OPTIONS=${TSAN_OPTIONS}" \
       \
       --pid=host \
       --init \
       \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       \
       /home/release-test-automation/release_tester/mixed_download_upgrade_test.py \
       --upgrade-matrix "${UPGRADE_MATRIX}" \
       --new-version "${NEW_VERSION}" \
       --do-not-run-test-suites \
       "${RTA_ARGS[@]}" \
       "${@}"
result=$?

# don't need docker stop $DOCKER_TAR_NAME
CLEANUP_DOCKER_ARGS=(
    -v "$(pwd)/../../:/oskar"
)
CLEANUP_PARAMS=(
    /oskar/work/
)
. ./jenkins/common/cleanup_ownership.sh
. ./jenkins/common/gather_coredumps.sh

if [ "$(find "$(pwd)/../" -name "*san*.log*" | wc -l )" -gt 0 ]; then
    7z a sanlogs "$(pwd)/../*san*.log*"
    printf "\nSan logs found after testrun:\n $(ls -l "$(pwd)/../"*san*.log*)\n" >> "$(pwd)/test_dir/testfailures.txt"
    rm -f "$(pwd)/../"*san*.log*
    mv sanlogs.7z "$(pwd)/test_dir/"
    echo "FAILED BY SAN-LOGS FOUND!"
    exit 1
fi

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED ${DOCKER_SUFFIX}!"
    exit 1
fi
