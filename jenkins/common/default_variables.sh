cat /proc/sys/kernel/core_pattern
ARCH="-$(uname -m)"

if test "${ARCH}" == "-x86_64"; then
    ARCH="-amd64"
else
    ARCH="-arm64v8"
fi

GIT_VERSION=$(git rev-parse --verify HEAD |sed ':a;N;$!ba;s/\n/ /g')
if test -z "$GIT_VERSION"; then
    GIT_VERSION=$VERSION
fi
if test -z "$OLD_VERSION"; then
    OLD_VERSION=3.11.0-nightly
fi
if test -z "$NEW_VERSION"; then
    NEW_VERSION=3.12.0-nightly
fi
if test -z "${PACKAGE_CACHE}"; then
    PACKAGE_CACHE="$(pwd)/package_cache/"
fi
RTA_ARGS=(  --git-version "$GIT_VERSION" )

ALLURE_DIR="$(pwd)/allure-results"
mkdir -p "${ALLURE_DIR}"
mkdir -p "$(pwd)/test_dir/tmp"
chmod a+rwxt "$(pwd)/test_dir/tmp"
