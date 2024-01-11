docker run -d \
       -p 9000:9000 \
       -p 9001:9001 \
       --network=$DOCKER_NETWORK_NAME \
       --name minio1 \
       -v "$(pwd)/test_dir/miniodata:/data" \
       -e "MINIO_ROOT_USER=minio" \
       -e "MINIO_ROOT_PASSWORD=minio123" \
       quay.io/minio/minio server /data --console-address ":9001" || exit 1
DOCKER_MINIO_CLEANUP1="docker kill minio1"
DOCKER_MINIO_CLEANUP2="docker rm minio1"
RTA_ARGS+=(--hb-mode s3bucket)
