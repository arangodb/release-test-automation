${DOCKER} run -d \
       -p 9000:9000 \
       -p 9001:9001 \
       --network=$DOCKER_NETWORK_NAME \
       --name minio1 \
       -v "$(pwd)/test_dir/miniodata:/data" \
       -e "MINIO_ROOT_USER=minio" \
       -e "MINIO_ROOT_PASSWORD=minio123" \
       quay.io/minio/minio server /data --console-address ":9001" || exit 1
TRAP_CLEANUP=(
    "${DOCKER} kill minio1"
    "${DOCKER} rm minio1"
    "${TRAP_CLEANUP[@]}"
)
RTA_ARGS+=(--hb-mode s3bucket)
