from ubuntu:20.04
MAINTAINER Wilfried Goesgens <willi@arangodb.com>

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get update ; \
    apt-get install -y python3-yaml python3-requests python3-click python3-distro python3-psutil python3-pexpect python3-pyftpdlib python3-statsd python3-pip gdb git; \
    rm -rf /var/lib/apt/lists/*
    
RUN pip3 install semver

# ENTRYPOINT ["/entrypoint.sh"]
