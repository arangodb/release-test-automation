#!/usr/bin/env python
""" set the jwt to the system prometheus agent """

from pathlib import Path
import psutil

from reporting.reporting_utils import step


@step
def set_prometheus_jwt(jwtstr):
    """alter the prometheus config to patch our current JWT into it"""
    cf_file = Path("/etc/prometheus/prometheus.token")
    cf_file.write_text(jwtstr, encoding="utf-8")
    restart = psutil.Popen(["/etc/init.d/prometheus-node-exporter", "restart"])
    restart.wait()
