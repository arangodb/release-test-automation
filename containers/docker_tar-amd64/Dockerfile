from ubuntu:20.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ARG PYTHON_VERSION="3.10.10"
ARG OPENSSL_VERSION="1.1.1t"
ARG PYENV_APP_VERSION="2.3.15"

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update ; \
    apt-get install -y build-essential curl gdb git libbz2-dev libffi-dev libgdbm-dev liblzma-dev libncurses5-dev libnss3-dev libreadline-dev libsqlite3-dev libssl-dev locales sudo systemd unzip wget zlib1g-dev \
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

RUN mkdir -p /home/entrypoint /home/release-test-automation /home/package_cache /home/versions /home/test_dir
# ADD tarball_nightly_test.py /home/entrypoint/tarball_nightly_test.py
# ENTRYPOINT ["/home/entrypoint/tarball_nightly_test.py"]
