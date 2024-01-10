from ubuntu:20.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ARG PYTHON_VERSION="3.10.10"
ARG OPENSSL_VERSION="1.1.1t"
ARG PYENV_APP_VERSION="2.3.15"

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV PYTHONPATH /home/release-test-automation/release_tester
ENV TZ=Europe/Berlin


RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update ; \
    apt-get install -y build-essential curl gdb git libbz2-dev libffi-dev libgdbm-dev liblzma-dev libncurses5-dev libnss3-dev libreadline-dev libsqlite3-dev libssl-dev locales sudo systemd unzip wget zlib1g-dev; \
 \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  || apt-get update -qqy \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* 

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

# Install python
RUN bash -l -c 'CONFIGURE_OPTS="--with-openssl=/usr/local --with-openssl-rpath=auto" pyenv install ${PYTHON_VERSION}'
RUN pyenv global ${PYTHON_VERSION}
RUN echo >> ~/.bashrc \
    && echo 'export PATH="/root/.pyenv/bin:$PATH"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Install python libraries
COPY requirements.txt /tmp/
RUN pyenv exec pip3 install -r /tmp/requirements.txt

# Replace system python with newly built
RUN rm /usr/bin/python3 ; \
    ln -s /usr/local/pyenv/shims/python3 /usr/bin/python3

RUN mkdir -p /home/release-test-automation \
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

RUN printf "passwd:      files\ngroup:       files\nhosts:       files dns" > /etc/nsswitch.conf

VOLUME [ "/sys/fs/cgroup" ]

# RUN ln -s /lib/systemd/systemd /usr/sbin/init
CMD /usr/sbin/init
