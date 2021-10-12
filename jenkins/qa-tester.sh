#!/bin/bash

# ./jenkins/qa-tester.sh upgrade 3.7.15 "3.6.15:3.7.15;3.7.14:3.7.15;3.7.15:3.8.1" ftp:stage2 --zip

TEST_FLOW=$1
shift
TEST_VERSION=$1
shift
if [ "${TEST_FLOW}" -eq "upgrade" ] || [ "${TEST_FLOW}" -eq "all" ]; then
  ALL_UPGRADES=$1
  shift
fi
TEST_SOURCE=$1
shift

ARGS=("${@}")

if [ "${TEST_FLOW}" -eq "all" ] || [ "${TEST_FLOW}" -eq "test" ]; then
  ./release_rester/full_download_test.py --new-version ${TEST_VERSION} --source ${TEST_SOURCE} ${ARGS}  
fi

if [ ! "${TEST_FLOW}" -eq "test" ]; then
  for testpair in ${ALL_UPGRADES//;/ }; do
      testset=("${testpair//:/ }")
      old_version=${testset[0]}
      new_version=${testset[1]}
      ./release_tester/full_download_upgrade.py \
        --old-version "${old_version}" \
        --old-source "${TEST_SOURCE}" \
        --new-version "${new_version}" \
        --new-source "${TEST_SOURCE}"
        ${ARGS}
  done
fi
