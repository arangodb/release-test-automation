from ubuntu:20.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV TZ=Europe/Berlin
ARG CHROME_VERSION="google-chrome-stable"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update ; \
    apt-get install -y python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd python3-pip gdb git python3-selenium fuse snapd snap-confine squashfuse sudo; \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update -qqy \
  && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
  && rm /etc/apt/sources.list.d/google-chrome.list \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/*




#     dpkg-divert --local --rename --add /sbin/udevadm &&\
#    ln -s /bin/true /sbin/udevadm
# RUN systemctl enable snapd
#VOLUME ["/sys/fs/cgroup"]
# STOPSIGNAL SIGRTMIN+3

RUN pip3 install semver
RUN mkdir -p /home/entrypoint /home/release-test-automation /home/package_cache /home/versions /home/test_dir
# ADD tarball_nightly_test.py /home/entrypoint/tarball_nightly_test.py
# ENTRYPOINT ["/home/entrypoint/tarball_nightly_test.py"]
