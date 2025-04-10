FROM centos:7
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV container docker
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV PYTHONPATH /home/release-test-automation/release_tester
ARG PYTHON_VERSION="3.10.10"
ARG OPENSSL_VERSION="1.1.1t"
ARG PYENV_APP_VERSION="2.3.15"

# COPY epel.repo /etc/yum.repos.d/epel.repo
RUN sed -i 's/mirrorlist=http:\/\/mirrorlist.centos.org/#mirrorlist=http:\/\/mirrorlist.centos.org/g' /etc/yum.repos.d/* &&\
    sed -i 's/#baseurl.*$/baseurl=http:\/\/vault.centos.org\/centos\/$releasever\/os\/$basearch/g' /etc/yum.repos.d/* &&\
    yum install -y http://archives.fedoraproject.org/pub/archive/epel/7/x86_64/Packages/e/epel-release-7-14.noarch.rpm
#
#

VOLUME [ "/sys/fs/cgroup" ]
run mkdir -p /home/release-test-automation \
 /home/package_cache \
 /home/versions \
 /home/entrypoint
RUN mkdir -p /home/entrypoint

RUN yum -y update; yum install -y bzip2-devel file gcc gdb git initscripts libffi-devel make ncurses-devel openssl11-devel openssl11-lib openssl-devel perl readline-devel sql xz-devel zlib-devel

#============================================
# Build newest python from source
#============================================
# Build OpenSSL from source
RUN curl -L https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz | (cd /usr/src; tar xz) ; \
    cd /usr/src/openssl-${OPENSSL_VERSION} && ./config --prefix=/usr/local && make -j`nproc` && make install ; \
    rm -rf /usr/src/openssl-${OPENSSL_VERSION}

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git /usr/local/pyenv && \
    cd /usr/local/pyenv && \
    git checkout v${PYENV_APP_VERSION} && \
    src/configure && make -C src && \
    rm -rf /usr/local/pyenv/src && \
    cd -
ENV PYENV_ROOT="/usr/local/pyenv"
ENV PATH="/usr/local/pyenv/bin:${PATH}"
RUN echo "export PYENV_ROOT=/usr/local/pyenv" >> /etc/environment && \
    echo "export PATH=$PATH" >> /etc/environment
RUN echo >> ~/.bashrc \
    && echo 'export PATH="/root/.pyenv/bin:$PATH"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Install python
RUN bash -l -c 'CFLAGS="$CFLAGS $(pkg-config --cflags openssl11)" LDFLAGS="$LDFLAGS $(pkg-config --libs openssl11)" CONFIGURE_OPTS="--with-openssl=/usr/local --with-openssl-rpath=auto" pyenv install ${PYTHON_VERSION}'
RUN source ~/.bashrc
RUN pyenv global ${PYTHON_VERSION}

# Install python libraries
COPY requirements.txt /tmp/
RUN pyenv exec pip3 install -r /tmp/requirements.txt

# Replace system python with newly built
RUN rm /usr/bin/python3 ; \
    ln -s /usr/local/pyenv/shims/python3 /usr/bin/python3

RUN (cd /lib/systemd/system/sysinit.target.wants/; for i in ; do [ $i == systemd-tmpfiles-setup.service ] || rm -f $i; done); \
  rm -rf /lib/systemd/system/multi-user.target.wants/;\
  rm -rf /etc/systemd/system/.wants/;\
  rm -rf /lib/systemd/system/local-fs.target.wants/;\
  rm -rf /lib/systemd/system/sockets.target.wants/udev;\
  rm -rf /lib/systemd/system/sockets.target.wants/initctl;\
  rm -rf /lib/systemd/system/basic.target.wants/;\
  rm -rf /lib/systemd/system/anaconda.target.wants/*;

RUN printf "passwd:      files\ngroup:       files\nhosts:       files dns" > /etc/nsswitch.conf

CMD ["/usr/sbin/init"]
