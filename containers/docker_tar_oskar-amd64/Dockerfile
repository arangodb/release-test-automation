from arangodb/ubuntubuildarangodb7-x86_64
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update ; \
    apt-get install -y wget unzip python3-yaml python3-requests python3-magic python3-click python3-distro python3-psutil python3-pexpect python3-statsd python3-pip  gdb git python3-selenium fuse snapd snap-confine squashfuse sudo python3-markdown python3-setuptools; \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir -p /home/entrypoint /home/release-test-automation /home/package_cache /home/versions /home/test_dir
