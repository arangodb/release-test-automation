#!/usr/bin/env python
""" Manage one instance of the arangobench
"""

import pathlib

import allure
import psutil
import yaml

import tools.loghelper as lh

BENCH_TODOS = {}

BENCH_COUNT = 0

def load_scenarios():
    """load the yaml testcases"""
    yamldir = pathlib.Path(__file__).parent.absolute() / ".." / ".." / "scenarios" / "arangobench"
    for one_yaml in yamldir.iterdir():
        if one_yaml.is_file():
            with open(one_yaml, encoding="utf8") as fileh:
                obj = yaml.load(fileh, Loader=yaml.Loader)
                for key in obj.keys():
                    if isinstance(obj[key], bool):
                        obj[key] = "true" if obj[key] else "false"
                BENCH_TODOS[one_yaml.name[:-4]] = obj

class ArangoBenchManager:
    """manages one arangobackup instance"""

    def __init__(self, basecfg, connect_instance):
        global BENCH_COUNT
        self.collection = f'arangobench_{BENCH_COUNT}'
        self.connect_instance = connect_instance
        self.arguments = None
        self.cfg = basecfg
        # fmt: off
        self.moreopts = [
            '-configuration', 'none',
            '--server.endpoint', self.connect_instance.get_endpoint(),
            '--server.username', str(self.cfg.username),
            '--server.password', str(self.cfg.passvoid),
            '--server.connection-timeout', '10',
            # else the wintendo may stay mute:
            '--log.force-direct', 'true',
            '--log.foreground-tty', 'true',
            '--collection', self.collection
        ]
        # fmt: on
        if self.cfg.verbose:
            self.moreopts += ["--log.level", "debug"]

        self.username = "testuser"
        self.passvoid = "testpassvoid"
        self.instance = None

    @allure.step
    def launch(self, testcase_no, moreopts=None):
        """run arangobench"""
        testcase = BENCH_TODOS[testcase_no]
        arguments = [self.cfg.real_bin_dir / "arangobench"] + self.moreopts
        if moreopts is not None:
            arguments.extend(moreopts)
        for key in testcase.keys():
            arguments.append("--" + key)
            arguments.append(str(testcase[key]))

        lh.log_cmd(arguments, self.cfg.verbose)
        self.arguments = arguments
        self.instance = psutil.Popen(arguments)
        print("az" * 40)

    def kill(self):
        """command to exit"""
        self.instance.kill()

    def wait(self):
        """wait for our instance to finish"""
        return self.instance.wait() == 0
