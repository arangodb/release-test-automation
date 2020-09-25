FROM debian:buster
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates apt-transport-https gnupg2 \
        python3-pip python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd gdb && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb

RUN pip3 install semver

RUN curl -OL https://download.arangodb.com/arangodb37/DEBIAN/Release.key && \
          apt-key add - < Release.key && \
          rm Release.key

RUN (echo 'deb https://download.arangodb.com/arangodb37/DEBIAN/ /' > /etc/apt/sources.list.d/arangodb.list) && \
    (echo arangodb3 arangodb3/password password test | debconf-set-selections) && \
    (echo arangodb3 arangodb3/password_again password test | debconf-set-selections) && \
    apt-get update && \
    DEBIAN_FRONTEND="noninteractive" apt-get install arangodb3 && \
    rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*.deb /var/lib/arangodb3 


RUN mkdir -p /home/test/release-test-automation

ADD "https://www.random.org/cgi-bin/randbyte?nbytes=10&format=h" skipcache

ENTRYPOINT ["/home/test/release-test-automation/entrypoint.sh"]
COPY release_tester/ /home/test/release-test-automation
COPY test_data/ /home/test/release-test-automation
COPY docker_me/entrypoint.sh /home/test/release-test-automation

