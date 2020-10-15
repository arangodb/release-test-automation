#!/usr/bin/env python
""" set the jwt to the system prometheus agent """

from pathlib import Path
import psutil

def set_prometheus_jwt(jwtstr):
    cf_file = Path('/etc/prometheus/prometheus.token')
    cf_file.write_text(jwtstr)
    r = psutil.Popen(['/etc/init.d/prometheus-node-exporter', 'restart'])
    r.wait()
