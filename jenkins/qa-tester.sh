#!/bin/bash


TEST_VERSION=$1
shift
ALL_TESTCASES=$1
shift
TEST_SOURCE=$1
shift

ARGS=("${@}")

for testpair in ${ALL_TESTCASES//;/ }; do
    testset=("${testpair//:/ }")
    old_version=${testset[0]}
    new_version=${testset[1]}
    if test "${old_version}" == "${TEST_VERSION}"; then
        ARGS+=('--old-version' "${TEST_VERSION}" --old-source "${TEST_SOURCE}")
    else
        ARGS+=('--old-version' "${old_version}" --old-source "public")
    fi

    if test "${new_version}" == "${TEST_VERSION}"; then
        ARGS+=('--new-version' "${TEST_VERSION}" --new-source "${TEST_SOURCE}")
    else
        ARGS+=('--new-version' "${new_version}" --new-source "public")
    fi

done

echo "${ARGS[@]}"

./release_tester/full_download_upgrade_test.py "${ARGS[@]}"
