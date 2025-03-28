${DOCKER} run \
       -v "/tmp:/tmp" \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "${ALLURE_DIR}:/home/allure-results" \
       -v "$(pwd)/test_dir/miniodata:/data" \
       "${CLEANUP_DOCKER_ARGS[@]}" \
       --rm \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results /data/* ${CLEANUP_PARAMS[@]}

rm -rf "$TMPDIR"
${DOCKER} run \
       -v /tmp/tmp:/tmp/ \
       --rm \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       rm -f /tmp/config.yml 
