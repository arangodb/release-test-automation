argv=$@
if [[ ${argv[@]} =~ "--selenium" ]]; then
    sed -e "s;@RTAROOT@;$(pwd);g" < "$(pwd)/selenoid_config/browsers.json.in" > "$(pwd)/selenoid_config/browsers.json"
    cat "$(pwd)/selenoid_config/browsers.json"
    ${DOCKER} pull aerokube/selenoid
    ${DOCKER} pull selenoid/chrome
    ${DOCKER} pull selenoid/video-recorder:latest-release
    mkdir -p "$(pwd)/test_dir/selenoid_video"
    SELENOID=$(${DOCKER} run -d --name selenoid -p 4444:4444 \
                      --network="${DOCKER_NETWORK_NAME}" \
                      -v "$(pwd)/test_dir/selenoid_video:/opt/selenoid/video" \
                      --env="OVERRIDE_VIDEO_OUTPUT_DIR=$(pwd)/test_dir/selenoid_video" \
                      -v /var/run/${DOCKER}.sock:/var/run/${DOCKER}.sock\
                      -v "$(pwd)/selenoid_config/:/etc/selenoid/:ro" \
                      aerokube/selenoid:latest-release -timeout 60m -container-network "${DOCKER_NETWORK_NAME}" )
    SELENOID_IP=$(${DOCKER} inspect \
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
    TRAP_CLEANUP+=(
        "${DOCKER} logs ${SELENOID}"
        "${DOCKER} stop ${SELENOID}"
        "${DOCKER} rm selenoid"
    )
    # bridgeid=$(${DOCKER} network ls | grep rta-bridge |sed "s; .*;;")
    # sudo tcpdump -ni "br-${bridgeid}" -w /tmp/out.pcap &
fi
