#!/usr/bin/env python
""" Manage one instance of the arangobench
"""

import pathlib

import allure
import psutil
import yaml

import tools.loghelper as lh

BENCH_TODOS = {}
def load_scenarios():
    """ load the yaml testcases """
    yamldir = pathlib.Path(__file__).parent.absolute() / '..' / '..' / 'scenarios' / 'arangobench'
    for one_yaml in yamldir.iterdir():
        if one_yaml.is_file():
            with open(one_yaml) as fileh:
                obj = yaml.load(fileh, Loader=yaml.Loader)
                for key in obj.keys():
                    if isinstance(obj[key], bool):
                        obj[key] = "true" if obj[key] else "false"
                BENCH_TODOS[one_yaml.name[:-4]] = obj

class ArangoBenchManager():
    """ manages one arangobackup instance"""
    def __init__(self, basecfg, connect_instance):
        self.connect_instance = connect_instance
        self.arguments = None
        self.cfg = basecfg
        self.moreopts = [
            '-configuration', 'none',
            '--server.endpoint', self.connect_instance.get_endpoint(),
            '--server.username', str(self.cfg.username),
            '--server.password', str(self.cfg.passvoid),
            '--server.connection-timeout', '10',
            # else the wintendo may stay mute:
            '--log.force-direct', 'true', '--log.foreground-tty', 'true'
        ]
        if self.cfg.verbose:
            self.moreopts += ['--log.level', 'debug']

        self.username = 'testuser'
        self.passvoid = 'testpassvoid'
        self.instance = None
    # pylint: disable=W0102
    @allure.step
    def launch(self, testcase_no, moreopts = []):
        """ run arangobench """
        testcase = BENCH_TODOS[testcase_no]
        arguments = [self.cfg.real_bin_dir / 'arangobench'] + self.moreopts + moreopts
        for key in testcase.keys():
            arguments.append('--' + key)
            arguments.append(str(testcase[key]))

        if self.cfg.verbose:
            lh.log_cmd(arguments)
        self.arguments = arguments
        self.instance = psutil.Popen(arguments)
        print("az"*40)

    def wait(self):
        """ wait for our instance to finish """
        return self.instance.wait() == 0
