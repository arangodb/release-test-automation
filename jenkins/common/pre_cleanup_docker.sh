
docker kill "$DOCKER_NAME" || true
docker rm "$DOCKER_NAME" || true

docker kill "minio1" || true
docker rm "minio1" || true

docker kill "selenoid" || true
docker rm "selenoid" || true

docker rm $DOCKER_NETWORK_NAME || true
mkdir -p "${PACKAGE_CACHE}"
mkdir -p test_dir/miniodata/home/test_dir
rm -rf test_dir/miniodata/home/test_dir/*
