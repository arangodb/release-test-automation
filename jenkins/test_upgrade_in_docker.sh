#!/bin/bash

mkdir -p /tmp/rpm_versions /tmp/deb_versions
docker_deb_name=arangodb/release-test-automation-deb:$(cat VERSION.json)
docker_rpm_name=arangodb/release-test-automation-rpm:$(cat VERSION.json)


trap "docker kill $docker_deb_name; docker rm $docker_deb_name; docker kill $docker_rpm_name; docker rm $docker_rpm_name;" EXIT
version=$(git rev-parse --verify HEAD)

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
          /home/release-test-automation/release_tester/tarball_nightly_test.py \
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
          /home/release-test-automation/release_tester/tarball_nightly_test.py \
          --no-zip $@; then
    echo "OK"
else
    echo "FAILED!"
    exit 1
fi


