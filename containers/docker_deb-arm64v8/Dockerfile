from ubuntu:18.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV PYTHONPATH /home/release-test-automation/release_tester
ENV TZ=Europe/Berlin

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update ; \
    apt-get install -y wget unzip sudo python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-statsd python3-pip python3-markdown gdb git systemd locales python3-selenium python3-certifi; \
 \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && apt-get update -qqy \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
  && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
  && locale-gen \
  && update-locale LANG=en_US.UTF-8

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt

run mkdir -p /home/release-test-automation \
 /home/package_cache \
 /home/versions \
 /home/entrypoint

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in ; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
  rm -rf /lib/systemd/system/multi-user.target.wants/;\
  rm -rf /etc/systemd/system/.wants/;\
  rm -rf /lib/systemd/system/local-fs.target.wants/;\
  rm -rf /lib/systemd/system/sockets.target.wants/udev;\
  rm -rf /lib/systemd/system/sockets.target.wants/initctl;\
  rm -rf /lib/systemd/system/basic.target.wants/;\
  rm -rf /lib/systemd/system/anaconda.target.wants/*;\
  rm -f /usr/sbin/policy-rc.d

VOLUME [ "/sys/fs/cgroup" ]
RUN ln -s /lib/systemd/systemd /usr/sbin/init
CMD /usr/sbin/init
