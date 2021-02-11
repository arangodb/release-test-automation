from ubuntu:18.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8     
ENV PYTHONPATH /home/release-test-automation/release_tester
ENV TZ=Europe/Berlin

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update ; \
    apt-get install -y python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd python3-pip gdb git systemd locales; \
    rm -rf /var/lib/apt/lists/* ; \
    sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen && \
    update-locale LANG=en_US.UTF-8 


RUN pip3 install semver

VOLUME /home/release-test-automation
VOLUME /home/package_cache
VOLUME /home/versions
RUN mkdir -p /home/entrypoint

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in ; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
  rm -rf /lib/systemd/system/multi-user.target.wants/;\
  rm -rf /etc/systemd/system/.wants/;\
  rm -rf /lib/systemd/system/local-fs.target.wants/;\
  rm -rf /lib/systemd/system/sockets.target.wants/udev;\
  rm -rf /lib/systemd/system/sockets.target.wants/initctl;\
  rm -rf /lib/systemd/system/basic.target.wants/;\
  rm -rf /lib/systemd/system/anaconda.target.wants/*;
VOLUME [ "/sys/fs/cgroup" ]
RUN ln -s /lib/systemd/systemd /usr/sbin/init
CMD /usr/sbin/init
