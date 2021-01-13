#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
import os
from pathlib import Path
from queue import Queue, Empty
from threading  import Thread

import psutil
import statsd
import requests
import yaml

from tools.timestamp import timestamp
import tools.interact as ti
from tools.interact import end_test
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager, StarterNonManager
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress
from tools.prometheus import set_prometheus_jwt

class testConfig():
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

statsdc = statsd.StatsClient('localhost', 8125)
RESULTS_TXT = None
OTHER_SH_OUTPUT = None
def result_line(line_tp):
    global OTHER_SH_OUTPUT, RESULTS_TXT
    if isinstance(line_tp, tuple):
        if line_tp[0].startswith(b'#'):
            str_line = str(line_tp[0])[6:-3]
            segments = str_line.split(',')
            if len(segments) < 3:
                print('n/a')
            else:
                str_line = ','.join(segments) + '\n'
                print(str_line)
                RESULTS_TXT.write(str_line)
                statsdc.timing(segments[0], float(segments[2]))
        else:
            OTHER_SH_OUTPUT.write(line_tp[1].get_endpoint() + " - " + str(line_tp[0]) + '\n')
            statsdc.incr('completed')

def makedata_runner(q, resq, arangosh, progressive_timeout):
    while True:
        try:
            # all tasks are already there. if done:
            job = q.get(timeout=0.1)
            print("starting my task! " + str(job['args']))
            res = arangosh.create_test_data("xx", job['args'], result_line=result_line, timeout=progressive_timeout)
            if not res[0]:
                if not self.cfg.verbose:
                    print("Script output: ")
                    print(res[1])
                print("error executing test - giving up.")
                resq.put(1)
                break
            resq.put(res)
        except Empty:
            print("No more work!")
            resq.put(-1)
            break

class ClusterPerf(Runner):
    """ this launches a cluster setup """
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst):
        global OTHER_SH_OUTPUT, RESULTS_TXT
        if not cfg.scenario.exists():
            cfg.scenario.write_text(yaml.dump(testConfig()))
            raise Exception("have written %s with default config" % str(cfg.scenario))

        with open(cfg.scenario) as fileh:
            self.scenario = yaml.load(fileh, Loader=yaml.Loader)

        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst, 'CLUSTER')
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())

        RESULTS_TXT = Path('/tmp/results.txt').open('w')
        OTHER_SH_OUTPUT = Path('/tmp/errors.txt').open('w')

    def starter_prepare_env_impl(self):
        mem = psutil.virtual_memory()
        os.environ['ARANGODB_OVERRIDE_DETECTED_TOTAL_MEMORY'] = str(int((mem.total * 0.8) / 9))

        self.create_test_collection = ("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""", "create test collection")

        self.basecfg.index = 0
        sm = None

        if self.remote:
            sm = StarterNonManager
        else:
            sm = StarterManager
        self.starter_instances.append(
            sm(self.basecfg,
               self.basedir, 'node1',
               mode='cluster',
               jwtStr=self.jwtdatastr,
               port=9528,
               expect_instances=[
                   InstanceType.agent,
                   InstanceType.coordinator,
                   InstanceType.dbserver,
               ],
               moreopts=[
               #    '--agents.agency.election-timeout-min=5',
               #    '--agents.agency.election-timeout-max=10',
               ]))
        self.starter_instances.append(
            sm(self.basecfg,
               self.basedir, 'node2',
               mode='cluster',
               jwtStr=self.jwtdatastr,
               port=9628,
               expect_instances=[
                   InstanceType.agent,
                   InstanceType.coordinator,
                   InstanceType.dbserver,
               ],
               moreopts=[
                   '--starter.join', '127.0.0.1:9528',
               #    '--agents.agency.election-timeout-min=5',
               #    '--agents.agency.election-timeout-max=10',
               ]))
        self.starter_instances.append(
            sm(self.basecfg,
               self.basedir, 'node3',
               mode='cluster',
               jwtStr=self.jwtdatastr,
               port=9728,
               expect_instances=[
                   InstanceType.agent,
                   InstanceType.coordinator,
                   InstanceType.dbserver,
               ],
               moreopts=[
                   '--starter.join', '127.0.0.1:9528',
               #    '--agents.agency.election-timeout-min=5',
               #    '--agents.agency.election-timeout-max=10',
               ]))
        for instance in self.starter_instances:
            instance.is_leader = True

    def make_data_impl(self):
        pass # we do this later.
    def check_data_impl_sh(self, arangosh):
        pass # we don't care
    def check_data_impl(self):
        pass
    def supports_backup_impl(self):
        return False # we want to do this on our own.

    def starter_run_impl(self):
        lh.subsection("instance setup")
        #if self.remote:
        #    logging.info("running remote, skipping")
        #    return
        for manager in self.starter_instances:
            logging.info("Spawning instance")
            manager.run_starter()

        logging.info("waiting for the starters to become alive")
        not_started = self.starter_instances[:] #This is a explicit copy
        while not_started:
            logging.debug("waiting for mananger with logfile:" + str(not_started[-1].log_file))
            if not_started[-1].is_instance_up():
                not_started.pop()
            progress('.')
            time.sleep(1)

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.detect_instance_pids()
            #self.basecfg.add_frontend('http', self.basecfg.publicip, str(node.get_frontend_port()))
        logging.info("instances are ready")

    def finish_setup_impl(self):
        if self.remote:
            logging.info("running remote, skipping")
            return

        self.agency_set_debug_logging()
        self.dbserver_set_debug_logging()
        self.coordinator_set_debug_logging()

        set_prometheus_jwt(self.starter_instances[0].get_jwt_header())

    def test_setup_impl(self):
        pass

    def wait_for_restore_impl(self, backup_starter):
        pass

    def upgrade_arangod_version_impl(self):
        pass

    def jam_attempt_impl(self):
        self.makedata_instances = self.starter_instances[:]
        logging.info('jamming: starting data stress')
        assert self.makedata_instances
        logging.debug("makedata instances")
        for i in self.makedata_instances:
            logging.debug(str(i))

        tcount = 0
        jobs = Queue()
        resultq = Queue()
        results = []
        workers = []
        no_dbs = self.scenario.db_count
        for i in range(self.scenario.db_count_chunks):
            jobs.put({
                'args': [
                    'TESTDB',
                    '--minReplicationFactor', str(self.scenario.min_replication_factor),
                    '--maxReplicationFactor', str(self.scenario.max_replication_factor),
                    '--dataMultiplier', str(self.scenario.data_multiplier),
                    '--numberOfDBs', str(no_dbs),
                    '--countOffset', str((i + self.scenario.db_offset) * no_dbs + 1),
                    '--collectionMultiplier', str(self.scenario.collection_multiplier),
                    '--singleShard', 'true' if self.scenario.single_shard else 'false',
                    ]
                })

        while len(workers) < self.scenario.parallelity:
            starter = self.makedata_instances[len(workers) % len(self.makedata_instances)]
            assert starter.arangosh
            arangosh = starter.arangosh

            #must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                workers.append(Thread(target=makedata_runner, args=(jobs, resultq, arangosh, self.scenario.progressive_timeout)))

        thread_count = len(workers)
        for worker in workers:
            worker.start()
            time.sleep(self.scenario.launch_delay)

        while tcount < thread_count:
            res_line = resultq.get()
            if isinstance(res_line, bytes):
                results.append(str(res_line).split(','))
            else:
                tcount += 1

        for worker in workers:
            worker.join()
        ti.prompt_user(self.basecfg, "DONE! press any key to shut down the SUT.")

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info('test ended')
