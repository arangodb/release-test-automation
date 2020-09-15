#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
from pathlib import Path
from queue import Queue, Empty
from threading  import Thread

import psutil
import statsd

from tools.timestamp import timestamp
import tools.interact as ti
from tools.interact import end_test
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

statsdc = statsd.StatsClient('localhost', 8125)
def result_line(line):
    if line.startswith(b'#'):
        line = str(line)[6:-3]
        segments = line.split(',')
        if len(segments) < 3:
            print('n/a')
        else:
            statsdc.timing(segments[0], float(segments[2]))
    else:
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
        #self.basecfg.frontends = []
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())

    def starter_prepare_env_impl(self):
        self.create_test_collection = ("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""", "create test collection")

        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node1',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9528,
                           expect_instances=[
                               InstanceType.agent,
                               InstanceType.coordinator,
                               InstanceType.dbserver,
                           ],
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node2',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9628,
                           expect_instances=[
                               InstanceType.agent,
                               InstanceType.coordinator,
                               InstanceType.dbserver,
                           ],
                           moreopts=['--starter.join', '127.0.0.1:9528']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node3',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9728,
                           expect_instances=[
                               InstanceType.agent,
                               InstanceType.coordinator,
                               InstanceType.dbserver,
                           ],
                           moreopts=['--starter.join', '127.0.0.1:9528']))
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

