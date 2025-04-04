export DOCKER=docker
export MOUNT_DOCKER_SOCKET=/var/run/${DOCKER}.sock:/var/run/${DOCKER}.sock
#if test -e /usr/bin/podman; then
#    echo "using podman"
#    DOCKER=podman
#    export REGISTRY_URL='docker.io/'
#    export MOUNT_DOCKER_SOCKET=/var/run/${DOCKER}/${DOCKER}.sock:/var/run/docker.sock
#    export CHOWN=false
#fi
