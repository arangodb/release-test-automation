${DOCKER} run -d \
       -p 9000:9000 \
       -p 9001:9001 \
       --network=$DOCKER_NETWORK_NAME \
       --name silo1 \
       -v "$(pwd)/test_dir/silodata:/data" \
       -e "MINIO_ROOT_USER=silo" \
       -e "MINIO_ROOT_PASSWORD=silo12345" \
       pgsty/silo server /data --console-address ":9001" || exit 1
TRAP_CLEANUP=(
    "${DOCKER} kill silo1"
    "${DOCKER} rm silo1"
    "${TRAP_CLEANUP[@]}"
)
RTA_ARGS+=(--hb-mode s3bucket)
