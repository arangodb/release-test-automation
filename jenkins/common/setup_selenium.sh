argv=$@
if [[ ${argv[@]} =~ "--selenium" ]]; then
    SELENOID=$(docker run -d --name selenoid -p 4444:4444 \
                      --network="${DOCKER_NETWORK_NAME}" \
                      -v /var/run/docker.sock:/var/run/docker.sock\
                      -v "$(pwd)/selenoid_config/:/etc/selenoid/:ro" \
                      aerokube/selenoid:latest-release -timeout 60m -container-network "${DOCKER_NETWORK_NAME}" )
    SELENOID_IP=$(docker inspect \
                         -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${SELENOID})
    echo "Selenoid IP: ${SELENOID_IP}"
    if test -z "${SELENOID_IP}"; then
        exit 1
    fi
    docker pull selenoid/chrome
    RTA_ARGS+=( --selenium-driver-args "command_executor=http://${SELENOID_IP}:4444/wd/hub")
    DOCKER_SELENOID_CLEANUP1="docker stop ${SELENOID}"
    DOCKER_SELENOID_CLEANUP2="docker rm selenoid"
fi
