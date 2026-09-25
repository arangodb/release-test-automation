
${DOCKER} kill "$DOCKER_NAME" || true
${DOCKER} rm "$DOCKER_NAME" || true

${DOCKER} kill "silo1" || true
${DOCKER} rm "silo1" || true

${DOCKER} kill "selenoid" || true
${DOCKER} rm "selenoid" || true

${DOCKER} network rm $DOCKER_NETWORK_NAME || true
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir/silodata/home/test_dir
rm -rf test_dir/silodata/home/test_dir/*
