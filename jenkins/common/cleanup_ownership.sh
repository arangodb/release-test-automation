docker run \
       -v "$(pwd)/test_dir:/home/test_dir" \
       -v "$(pwd)/allure-results:/home/allure-results" \
       -v "$(pwd)/test_dir/miniodata:/data" \
       --rm \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       chown -R "$(id -u):$(id -g)" /home/test_dir /home/allure-results /data/*

docker run \
       -v /tmp/tmp:/tmp/ \
       --rm \
       "${DOCKER_NAMESPACE}${DOCKER_TAG}" \
       rm -f /tmp/config.yml 
