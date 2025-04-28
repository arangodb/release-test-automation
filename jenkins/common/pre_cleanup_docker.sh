
${DOCKER} kill "$DOCKER_NAME" || true
${DOCKER} rm "$DOCKER_NAME" || true

${DOCKER} kill "minio1" || true
${DOCKER} rm "minio1" || true

${DOCKER} kill "selenoid" || true
${DOCKER} rm "selenoid" || true

${DOCKER} network rm $DOCKER_NETWORK_NAME || true
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir/miniodata/home/test_dir
rm -rf test_dir/miniodata/home/test_dir/*
