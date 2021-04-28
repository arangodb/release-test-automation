#!/bin/bash -x

cd /home/test/release-test-automation

python3 release_tester/perf.py --version 3.8.0-devel --no-enterprise --package-dir /tmp/ --mode tests $@
