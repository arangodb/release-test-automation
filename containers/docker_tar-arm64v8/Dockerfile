from ubuntu:20.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update ; \
    apt-get install -y wget unzip python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-statsd python3-pip python-certifi gdb git python3-selenium fuse snapd snap-confine squashfuse sudo python3-markdown; \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && apt-get update -qqy \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir -p /home/entrypoint /home/release-test-automation /home/package_cache /home/versions /home/test_dir
# ADD tarball_nightly_test.py /home/entrypoint/tarball_nightly_test.py
# ENTRYPOINT ["/home/entrypoint/tarball_nightly_test.py"]