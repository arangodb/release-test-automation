argv=$@
if [[ ${argv[@]} =~ "--selenium" ]]; then
    mkdir -p "$(pwd)/test_dir/selenoid_video"
    docker pull selenoid/video-recorder
    docker pull selenoid/chrome
    SELENOID=$(docker run -d --name selenoid -p 4444:4444 \
                      --network="${DOCKER_NETWORK_NAME}" \
                      -v "$(pwd)/test_dir/selenoid_video:/opt/selenoid/video" \
                      --env="OVERRIDE_VIDEO_OUTPUT_DIR=$(pwd)/test_dir/selenoid_video" \
                      -v /var/run/docker.sock:/var/run/docker.sock\
                      -v "$(pwd)/selenoid_config/:/etc/selenoid/:ro" \
                      aerokube/selenoid:latest-release -timeout 60m -container-network "${DOCKER_NETWORK_NAME}" )
    SELENOID_IP=$(docker inspect \
                         -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ${SELENOID})
    echo "Selenoid IP: ${SELENOID_IP}"
    if test -z "${SELENOID_IP}"; then
        exit 1
    fi
    RTA_ARGS+=(
        --selenium-driver-args "command_executor=http://${SELENOID_IP}:4444/wd/hub"
        --selenium-driver-args selenoid:options=enableVideo=True
        --selenium-driver-args browserName=chrome
        --selenium-driver-args browserVersion=latest
    )
    DOCKER_SELENOID_CLEANUP1="docker stop ${SELENOID}"
    DOCKER_SELENOID_CLEANUP2="docker rm selenoid"
    # bridgeid=$(docker network ls | grep rta-bridge |sed "s; .*;;")
    # sudo tcpdump -ni "br-${bridgeid}" -w /tmp/out.pcap &
fi
