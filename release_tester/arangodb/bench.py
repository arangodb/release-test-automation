#!/usr/bin/env python
""" Manage one instance of the arangobench
"""

import logging
import json
import re
import subprocess
import time

import psutil

from tools.asciiprint import ascii_print, print_progress as progress
import tools.loghelper as lh

benchTodos = [{
  'requests': '10000',
  'concurrency': '2',
  'test-case': 'version',
  'keep-alive': 'false'
}, {
  'requests': '10000',
  'concurrency': '2',
  'test-case': 'version',
  'async': 'true'
}, {
  'requests': '20000',
  'concurrency': '1',
  'test-case': 'version',
  'async': 'true'
}, {
  'requests': '10000',
  'concurrency': '3',
  'test-case': 'stream-cursor',
  'complexity': '4'
}, {
  'requests': '100000',
  'concurrency': '2',
  'test-case': 'shapes',
  'batch-size': '16',
  'complexity': '2'
}, {
  'requests': '100000',
  'concurrency': '2',
  'test-case': 'shapes-append',
  'batch-size': '16',
  'complexity': '4'
}, {
  'requests': '100000',
  'concurrency': '2',
  'test-case': 'random-shapes',
  'batch-size': '16',
  'complexity': '2'
}, {
  'requests': '1000',
  'concurrency': '2',
  'test-case': 'version',
  'batch-size': '16'
}, {
  'requests': '100',
  'concurrency': '1',
  'test-case': 'version',
  'batch-size': '0'
}, {
  'requests': '100',
  'concurrency': '2',
  'test-case': 'document',
  'batch-size': '10',
  'complexity': '1'
}, { # this one
  'requests': '4000000',
  'concurrency': '2',
  'test-case': 'crud',
  'complexity': '1'
}, {
  'requests': '4000',
  'concurrency': '2',
  'test-case': 'crud-append',
  'complexity': '4'
}, {
  'requests': '4000',
  'concurrency': '2',
  'test-case': 'edge',
  'complexity': '4'
}, {
  'requests': '5000',
  'concurrency': '2',
  'test-case': 'hash',
  'complexity': '1'
}, {
  'requests': '5000',
  'concurrency': '2',
  'test-case': 'skiplist',
  'complexity': '1'
}, { # this one
  'requests': '500000',
  'concurrency': '3',
  'test-case': 'aqltrx',
  'complexity': '1',
}, {
  'requests': '1000',
  'concurrency': '4',
  'test-case': 'aqltrx',
  'complexity': '1',
}, {
  'requests': '100',
  'concurrency': '3',
  'test-case': 'counttrx',
}, {
  'requests': '500',
  'concurrency': '3',
  'test-case': 'multitrx',
}];



class ArangoBenchManager():
    """ manages one arangobackup instance"""
    def __init__(self,
                 basecfg,connect_instance):
        self.connect_instance = connect_instance

        self.cfg = basecfg
        self.moreopts = [
            '--server.endpoint', self.connect_instance.get_endpoint(),
            '--server.username', str(self.cfg.username),
            '--server.password', str(self.cfg.passvoid),
            '--server.connection-timeout', '10',
            # else the wintendo may stay mute:
            '--log.force-direct', 'true', '--log.foreground-tty', 'true'
        ]
        if self.cfg.verbose:
            self.moreopts += ["--log.level=debug"]

        self.username = 'testuser'
        self.passvoid = 'testpassvoid'
        self.instance = None

    def launch(self, testcase_no):
        testcase = benchTodos[testcase_no]
        
        arguments = [self.cfg.bin_dir / 'arangobench'] + self.moreopts
        for key in testcase.keys():
            arguments.append('--' + key)
            arguments.append(testcase[key])

        if self.cfg.verbose:
            lh.log_cmd(arguments)

        self.instance = psutil.Popen(arguments)
        print("az"*40)
                             
    def wait(self):
        self.instance.wait()
