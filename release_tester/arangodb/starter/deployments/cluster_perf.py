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

from tools.timestamp import timestamp
import tools.interact as ti
from tools.interact import end_test
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager, StarterNonManager
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

statsdc = statsd.StatsClient('localhost', 8125)
resultstxt = Path('/tmp/results.txt').open('w')
otherShOutput = Path('/tmp/errors.txt').open('w')
def result_line(line_tp):
    if isinstance(line_tp, tuple):
        if line_tp[0].startswith(b'#'):
            str_line = str(line_tp[0])[6:-3]
            segments = str_line.split(',')
            if len(segments) < 3:
                print('n/a')
            else:
                str_line = ','.join(segments) + '\n'
                print(str_line)
                resultstxt.write(str_line)
                statsdc.timing(segments[0], float(segments[2]))
        else:
            otherShOutput.write(line_tp[1].get_endpoint() + " - " + str(line_tp[0]) + '\n')
            statsdc.incr('completed')

def makedata_runner(q, resq, arangosh):
    while True:
        try:
            # all tasks are already there. if done:
            job = q.get(timeout=0.1)
            print("starting my task! " + str(job['args']))
            res = arangosh.create_test_data("xx", job['args'], result_line=result_line)
            if not res:
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
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst, 'CLUSTER')
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())

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
                   '--agents.agency.election-timeout-min=5',
                   '--agents.agency.election-timeout-max=10',
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
                   '--agents.agency.election-timeout-min=5',
                   '--agents.agency.election-timeout-max=10',
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
                   '--agents.agency.election-timeout-min=5',
                   '--agents.agency.election-timeout-max=10',
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

        for starter_mgr in self.starter_instances:
            starter_mgr.send_request(InstanceType.agent,
                                     requests.put,
                                     '/_admin/log/level',
                                     '{"agency":"debug"}');

        jwtstr = self.starter_instances[0].get_jwt_header()
        cf_file = Path('/etc/prometheus/prometheus.token')
        cf_file.write_text(jwtstr)
        r = psutil.Popen(['/etc/init.d/prometheus-node-exporter', 'restart'])
        r.wait()

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

        interactive = self.basecfg.interactive
        tcount = 0
        offset = 0
        jobs = Queue()
        resultq = Queue()
        results = []
        workers = []
        no_dbs = 100
        for i in range(5):
            jobs.put({
                'args': [
                    'TESTDB',
                    '--minReplicationFactor', '1',
                    '--maxReplicationFactor', '2',
                    '--dataMultiplier', '4',
                    '--numberOfDBs', str(no_dbs),
                    '--countOffset', str(i * no_dbs +1),
                    '--collectionMultiplier', '1',
                    '--singleShard', 'false'
                    ]
                })

        for starter in self.makedata_instances:
            assert starter.arangosh
            arangosh = starter.arangosh

            #must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                workers.append(Thread(target=makedata_runner, args=(jobs, resultq, arangosh)))

        thread_count = len(workers)
        for worker in workers:
            worker.start()
            time.sleep(1.3)

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

