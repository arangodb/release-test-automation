export DOCKER=docker

if test -e /usr/bin/podman; then
    echo "using podman"
    DOCKER=podman
    export REGISTRY_URL='docker.io/'
    export CHOWN=false
fi
