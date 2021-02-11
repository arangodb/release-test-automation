FROM centos:7
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV container docker
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8     
ENV PYTHONPATH /home/release-test-automation/release_tester

VOLUME [ "/sys/fs/cgroup" ]
VOLUME /home/release-test-automation
VOLUME /home/package_cache
VOLUME /home/versions
RUN mkdir -p /home/entrypoint

RUN yum update ; yum install -y python3 python3-pyyaml python36-PyYAML python3-requests python3-click gcc platform-python-devel python3-distro python3-devel python36-distro python36-click python36-pexpect python3-pexpect python3-pyftpdlib;
# RUN pip3 install psutil semver

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in ; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
  rm -rf /lib/systemd/system/multi-user.target.wants/;\
  rm -rf /etc/systemd/system/.wants/;\
  rm -rf /lib/systemd/system/local-fs.target.wants/;\
  rm -rf /lib/systemd/system/sockets.target.wants/udev;\
  rm -rf /lib/systemd/system/sockets.target.wants/initctl;\
  rm -rf /lib/systemd/system/basic.target.wants/;\
  rm -rf /lib/systemd/system/anaconda.target.wants/*;

CMD ["/usr/sbin/init"]
