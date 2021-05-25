#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from datetime import datetime
import time
import logging
import os
import copy
import pprint
import shutil

from pathlib import Path
from queue import Queue, Empty
from threading  import Thread, Lock

import psutil
import yaml

from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner

from tools.asciiprint import print_progress as progress
from tools.timestamp import timestamp


pp = pprint.PrettyPrinter(indent=4)


# pylint: disable=W0603

class TestConfig():
    """ this represents one tests configuration """
    # pylint: disable=R0902 disable=R0903
    def __init__(self):
        self.parallelity = 3
        self.db_count = 100
        self.db_count_chunks = 5
        self.min_replication_factor = 2
        self.max_replication_factor = 3
        self.data_multiplier = 4
        self.collection_multiplier = 1
        self.launch_delay = 1.3
        self.single_shard = False
        self.db_offset = 0
        self.progressive_timeout = 100

#statsdc = statsd.StatsClient('localhost', 8125)
# RESULTS_TXT = None
# OTHER_SH_OUTPUT = None
# def result_line(line_tp):
#     """ get one result line """
#     global OTHER_SH_OUTPUT, RESULTS_TXT
#     if isinstance(line_tp, tuple):
#         if line_tp[0].startswith(b'#'):
#             str_line = str(line_tp[0])[6:-3]
#             segments = str_line.split(',')
#             if len(segments) < 3:
#                 print('n/a')
#             else:
#                 str_line = ','.join(segments) + '\n'
#                 # print(str_line)
#                 RESULTS_TXT.write(str_line)
#                 # statsdc.timing(segments[0], float(segments[2]))
#         else:
#             OTHER_SH_OUTPUT.write(line_tp[1].get_endpoint() +
#                                   " - " + str(line_tp[0]) + '\n')
#             statsdc.incr('completed')

def testing_runner(testing_instance, this, arangosh):
    """ operate one makedata instance """
    arangosh.run_testing(this['suite'],
                         this['args'],
                         999999999,
                         this['base_thislogdir'],
                         this['log_file'],
                         True)
    print('done with ' + this['name'])
    this['crashed' ] = this['crashed_file'].read_text() == "true"
    this['success' ] = this['success_file'].read_text() == "true"
    this['structured_results' ] = this['crashed_file'].read_text()
    this['summary' ] = this['summary_file'].read_text()

    if this['crashed' ] or not this['success' ]:
        print(str(this['log_file'].name))
        print(this['log_file'].parent / ("FAIL_" + str(this['log_file'].name))
              )
        failname = this['log_file'].parent / ("FAIL_" + str(this['log_file'].name))
        this['log_file'].rename(failname)
        this['log_file'] = failname
        # raise Exception("santehusanotehusanotehu")
    
    testing_instance.done_job(this['weight'])

def convert_args(args):
    ret_args = []
    for one_arg in args:
        if isinstance(one_arg, bool):
            ret_args.append("true" if one_arg else "false")
        else:
            ret_args.append(one_arg)
    return ret_args

def set_filenames(suite):
    suite['base_testdir'] = Path.cwd() / 'tmp'
    suite['base_logdir' ] = Path.cwd() / 'testrun'
    suite['base_thislogdir'] = suite['base_testdir'] / suite['log']
    suite['log_file'] =  suite['base_logdir'] / (str(suite['log']) + '.log')
    suite['summary_file'] = suite['base_thislogdir'] / 'testfailures.txt'
    suite['crashed_file'] = suite['base_thislogdir'] / 'UNITTEST_RESULT_CRASHED.json'
    suite['success_file'] = suite['base_thislogdir'] / 'UNITTEST_RESULT_EXECUTIVE_SUMMARY.json'
    suite['report_file'] =  suite['base_thislogdir'] / 'UNITTEST_RESULT.json'

def create_scenario(scenarios, testsuite, test_content):
    args = []
    suffix = ""
    if test_content['mode'] == "cluster":
        args += ["--cluster", "true"]
    elif test_content['mode'] == "single":
        pass
    elif test_content['mode'] == "active_failover":
        args += ["--active", "true"]
    else:
        raise Exception("don't know test mode " + test_content['mode'])
    if 'suffix' in test_content:
        suffix = '_' + test_content['suffix']
    weight = 1
    if 'weight' in test_content:
        weight = int(test_content['weight'])
    if 'args' in test_content:
        args += convert_args(test_content['args'])
    suite = {
        'args': args,
        'suite': testsuite,
        'name': testsuite,
        'log': Path(testsuite +
                    suffix + '_' +
                    test_content['mode']),
        'weight': weight
    }
    # Path.cwd() / 'testrun'
    if 'buckets' in test_content:
        n_buckets = int(test_content['buckets'])
        for bucket in range(0, n_buckets):
            this_bucket = copy.deepcopy(suite)
            this_bucket['name'] += "_" + str(bucket)
            this_bucket['log'] = Path( # testsuite +
                                               this_bucket['name'] +
                                               suffix + '_' +
                                               test_content['mode'])
            this_bucket['args'] += ['--testBuckets', str(n_buckets) + '/' + str(bucket)]
            scenarios.append(this_bucket)
            set_filenames(this_bucket)
    else:
        scenarios.append(suite)
        set_filenames(suite)

def parse_scenario(yml_file, scenarios):
    if not yml_file.name.endswith('.yml'):
        return
    testsuite = yml_file.name[:-4]
    ymldoc = yml_file.read_text()
    print(ymldoc)
    yml_content = yaml.load(ymldoc, Loader=yaml.Loader)
    pp.pprint(yml_content)
    for suite in yml_content['tests']:
        pp.pprint(suite)
        create_scenario(scenarios, testsuite, suite)

class Testing(Runner):
    """ this launches a cluster setup """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst, selenium, selenium_driver_args):
        global OTHER_SH_OUTPUT, RESULTS_TXT
        #if not cfg.scenario.exists():
        #    cfg.scenario.write_text(yaml.dump(TestConfig()))
        #    raise Exception("have written %s with default config" % str(cfg.scenario))

        self.scenarios = []
        for scenario in cfg.scenario.iterdir():
            if scenario.is_file():
                parse_scenario(scenario, self.scenarios)
            else:
                print('no: ' + str(scenario))
        pp.pprint(self.scenarios)
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst,
                         'TESTING', 1, 1, selenium, selenium_driver_args, "xx")
        self.success = False
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.slot_lock = Lock()
        #RESULTS_TXT = Path('/tmp/results.txt').open('w')
        #OTHER_SH_OUTPUT = Path('/tmp/errors.txt').open('w')

    def done_job(self, count):
        with self.slot_lock:
            self.used_slots -= count

    def launch_next(self, offset):
        if self.scenarios[offset]['weight'] > (self.available_slots - self.used_slots):
            return False
        with self.slot_lock:
            self.used_slots += self.scenarios[offset]['weight']
        this = self.scenarios[offset]
        print("launching " + this['name'])
        pp.pprint(this)

        print(this['log'])
        worker = Thread(target=testing_runner,
                        args=(self,
                              this,
                              self.old_installer.arangosh))
        worker.start()
        return True
        
    def starter_prepare_env_impl(self):
        mem = psutil.virtual_memory()
        os.environ['ARANGODB_OVERRIDE_DETECTED_TOTAL_MEMORY'] = str(int((mem.total * 0.8) / 9))

        self.available_slots = psutil.cpu_count() / 4 # TODO well threadripper..
        self.used_slots = 0
        #raise Exception("tschuess")
        start_offset = 0
        used_slots = 0
        some_scenario = self.scenarios[0]
        if not some_scenario['base_logdir'].exists():
            some_scenario['base_logdir'].mkdir()
        if not some_scenario['base_testdir'].exists():
            some_scenario['base_testdir'].mkdir()
        os.environ['TMPDIR'] = str(some_scenario['base_testdir'])
        os.environ['TEMP'] = str(some_scenario['base_testdir']) # TODO howto wintendo?
        while start_offset < len(self.scenarios) or used_slots > 0:
            used_slots = 0
            with self.slot_lock:
                used_slots = self.used_slots
            if self.available_slots > used_slots:
                if start_offset < len(self.scenarios) and self.launch_next(start_offset):
                    start_offset += 1
                    time.sleep(5)
                else:
                    if used_slots == 0:
                        print("done")
                        break
                    print('elsesleep')
                    time.sleep(5)
            else:
                print('elseelsesleep')
                time.sleep(5)
        self.basecfg.index = 0
        print(self.scenarios)
        summary = ""
        for testrun in self.scenarios:
            if testrun['crashed' ] or not testrun['success' ]:
                summary += testrun['summary']
        print("\n")
        print(summary)

        (some_scenario['base_logdir'] / 'testfailures.txt').write_text(summary)
        print(                            some_scenario['base_testdir'])
        shutil.make_archive(some_scenario['base_logdir'] / 'innerlogs',
                            "tar",
                            Path.cwd(),
                            str(some_scenario['base_testdir']) + "/")

        tarfn = datetime.now(tz=None).strftime("testreport-%d-%b-%YT%H.%M.%SZ")
        print(some_scenario['base_logdir'])
        shutil.make_archive(tarfn,
                            "bztar",
                            str(some_scenario['base_logdir']) + "/",
                            str(some_scenario['base_logdir']) + "/")
        
    def jam_attempt_impl(self):
        pass

    def make_data_impl(self):
        pass # we do this later.
    def check_data_impl_sh(self, arangosh):
        pass # we don't care
    def check_data_impl(self):
        pass
    def supports_backup_impl(self):
        return False # we want to do this on our own.

    def starter_run_impl(self):
        pass

    def finish_setup_impl(self):
        pass

    def test_setup_impl(self):
        pass

    def wait_for_restore_impl(self, backup_starter):
        pass

    def upgrade_arangod_version_impl(self):
        pass


    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info('test ended')

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
