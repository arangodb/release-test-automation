#!/bin/bash

VERSION=$(cat VERSION.json)
GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.8.0-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.9.0-nightly
fi
if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="${WORKSPACE}/package_cache/"
fi

force_arg=()
if test -n "$FORCE" -o "$TEST_BRANCH" != 'main'; then
  force_arg=(--force)
fi

if test -n "$SOURCE"; then
    force_arg+=(--old-source "$SOURCE" --new-source "$SOURCE")
fi

VERSION_TAR_NAME="${OLD_VERSION}_${NEW_VERSION}_tar_version.tar"
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir
mkdir -p allure-results


$(pwd)/release_tester/full_download_upgrade.py \
      --version-state-tar "${WORKSPACE}/${VERSION_TAR_NAME}" \
      --package-dir "${PACKAGE_CACHE}" \
      --old-version "${OLD_VERSION}" \
      --new-version "${NEW_VERSION}" \
      --no-zip \
      --verbose \
      --alluredir ${WORKSPACE}/allure-results \
      --git-version "$GIT_VERSION" \
      "${force_arg[@]}" \
      "${@}"
result=$?

if test "${result}" -eq "0"; then
    echo "OK"
else
    echo "FAILED TAR!"
    exit 1
fi