from ubuntu:18.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV PYTHONPATH /home/release-test-automation/release_tester
ENV TZ=Europe/Berlin
ARG CHROME_VERSION="google-chrome-stable"
ARG PYTHON_VERSION="3.10.10"
ARG OPENSSL_VERSION="1.1.1t"
ARG PYENV_APP_VERSION="2.3.15"
ARG PYENV_VIRTUALENV_VERSION="1.2.1"

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt-get update ; \
    apt-get install -y build-essential curl gdb git libbz2-dev libffi-dev libgdbm-dev liblzma-dev libncurses5-dev libnss3-dev libreadline-dev libsqlite3-dev libssl-dev locales sudo systemd unzip wget zlib1g-dev; \
    \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
  && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update -qqy \
  && apt-get -qqy install \
    ${CHROME_VERSION:-google-chrome-stable} \
  && rm -f /etc/apt/sources.list.d/google-chrome.list \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
  && sed -i '/en_US.UTF-8/s/^# //g' /etc/locale.gen \
  && locale-gen \
  && update-locale LANG=en_US.UTF-8

#=================================
# Chrome Launch Script Wrapper
#=================================
COPY wrap_chrome_binary /opt/bin/wrap_chrome_binary
RUN /opt/bin/wrap_chrome_binary


#============================================
# Chrome webdriver
#============================================
# can specify versions by CHROME_DRIVER_VERSION
# Latest released version will be used by default
#============================================
ARG CHROME_DRIVER_VERSION
RUN if [ -z "$CHROME_DRIVER_VERSION" ]; \
  then CHROME_MAJOR_VERSION=$(google-chrome --version | sed -E "s/.* ([0-9]+)(\.[0-9]+){3}.*/\1/") \
    && CHROME_DRIVER_VERSION=$(wget --no-verbose -O - "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR_VERSION}"); \
  fi \
  && echo "Using chromedriver version: "$CHROME_DRIVER_VERSION \
  && wget --no-verbose -O /tmp/chromedriver_linux64.zip \
       https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip \
  && rm -rf /opt/selenium/chromedriver \
  && unzip /tmp/chromedriver_linux64.zip -d /opt/selenium \
  && rm -f /tmp/chromedriver_linux64.zip \
  && mv /opt/selenium/chromedriver /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION \
  && chmod 755 /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION \
  && sudo ln -fs /opt/selenium/chromedriver-$CHROME_DRIVER_VERSION /usr/bin/chromedriver

#============================================
# Build newest python from source
#============================================
# Build OpenSSL from source
RUN curl -L https://www.openssl.org/source/openssl-${OPENSSL_VERSION}.tar.gz | (cd /usr/src; tar xz)
RUN cd /usr/src/openssl-${OPENSSL_VERSION} && ./config --prefix=/usr/local && make -j`nproc` && make install

# Install pyenv
RUN git clone https://github.com/pyenv/pyenv.git /usr/local/pyenv && \
    cd /usr/local/pyenv && \
    git checkout v${PYENV_APP_VERSION} && \
    src/configure && make -C src && \
    cd - && \
    git clone https://github.com/pyenv/pyenv-virtualenv.git /usr/local/pyenv/plugins/pyenv-virtualenv && \
    cd /usr/local/pyenv/plugins/pyenv-virtualenv && \
    git checkout v${PYENV_VIRTUALENV_VERSION} && \
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
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc \
    && echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Install python libraries
COPY requirements.txt /tmp/
RUN pyenv exec pip3 install -r /tmp/requirements.txt

# Replace system python with newly built
RUN rm /usr/bin/python3 ; \
    ln -s /usr/local/pyenv/shims/python3 /usr/bin/python3

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
