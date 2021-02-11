#!/bin/bash

mkdir -p /tmp/rpm_versions /tmp/deb_versions
docker kill docker_deb docker_rpm
docker rm docker_deb; docker_rpm; 

docker build docker_deb -t docker_deb
docker build docker_rpm -t docker_rpm

trap "docker kill docker_deb; \
    docker rm docker_deb; \
    docker kill docker_rpm; \
    docker rm docker_rpm" EXIT


docker run -itd \
       --privileged \
       --name=docker_deb \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v `pwd`:/home/release-test-automation \
       -v `pwd`/package_cache/:/home/package_cache \
       -v /tmp:/home/test_dir \
       -v /tmp/tmp:/tmp/ \
       -v /tmp/deb_versions:/home/versions \
       \
       docker_deb \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec docker_deb \
          python3 /home/release-test-automation/docker_tar/tarball_nightly_test.py \
          --no-zip $@; then
    echo "OK"
else
    echo "FAILED!"
    exit 1
fi


docker run \
       -v /sys/fs/cgroup:/sys/fs/cgroup:ro \
       -v `pwd`:/home/release-test-automation \
       -v `pwd`/package_cache/:/home/package_cache \
       -v /tmp:/home/test_dir \
       -v /tmp/tmp:/tmp/ \
       -v /tmp/rpm_versions:/home/versions \
       \
       --privileged \
       --name=docker_rpm \
       -itd \
       \
       docker_rpm \
       \
       /lib/systemd/systemd --system --unit=multiuser.target 

if docker exec docker_rpm \
          /home/release-test-automation/docker_tar/tarball_nightly_test.py \
          --no-zip $@; then
    echo "OK"
else
    echo "FAILED!"
    exit 1
fi


