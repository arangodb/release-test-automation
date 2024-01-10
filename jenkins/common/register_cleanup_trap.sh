trap 'docker kill "${DOCKER_NAME}";
      docker rm "${DOCKER_NAME}";
      ${DOCKER_MINIO_CLEANUP1};
      ${DOCKER_MINIO_CLEANUP2};
      ${DOCKER_SELENOID_CLEANUP1};
      ${DOCKER_SELENOID_CLEANUP2};
      docker network rm ${DOCKER_NETWORK_NAME};
     ' EXIT
