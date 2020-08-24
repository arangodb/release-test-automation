#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
from pathlib import Path

from tools.timestamp import timestamp
from tools.interact import end_test
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress


class Cluster(Runner):
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
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node2',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9628,
                           moreopts=['--starter.join', '127.0.0.1:9528']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node3',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9728,
                           moreopts=['--starter.join', '127.0.0.1:9528']))
        for instance in self.starter_instances:
            instance.is_leader = True

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
        self.makedata_instances = self.starter_instances[:]

    def test_setup_impl(self):
        pass

    def wait_for_restore_impl(self, backup_starter):
        for starter in self.starter_instances:
            for dbserver in starter.get_dbservers():
                dbserver.detect_restore_restart()

    def upgrade_arangod_version_impl(self):
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)

        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        self.starter_instances[1].wait_for_upgrade()

    def jam_attempt_impl(self):
        logging.info("stopping instance 2")
        self.starter_instances[2].terminate_instance()

        end_test(self.basecfg, "instance stopped")
        # respawn instance, and get its state fixed
        self.starter_instances[2].respawn_instance()
        while not self.starter_instances[2].is_instance_up():
            progress('.')
            time.sleep(1)
        print()
        self.starter_instances[2].detect_instances()
        self.starter_instances[2].detect_instance_pids()
        self.starter_instances[2].detect_instance_pids_still_alive()

        logging.info('jamming: Starting instance without jwt')
        dead_instance = StarterManager(
            self.basecfg,
            Path('CLUSTER'), 'nodeX',
            mode='cluster',
            jwtStr=None,
            moreopts=['--starter.join', '127.0.0.1'])
        dead_instance.run_starter()

        i = 0
        while True:
            logging.info(". %d", i)
            if not dead_instance.is_instance_running():
                break
            if i > 40:
                logging.info('Giving up wating for the starter to exit')
                raise Exception("non-jwt-ed starter won't exit")
            i += 1
            time.sleep(10)
        logging.info(str(dead_instance.instance.wait(timeout=320)))
        logging.info('dead instance is dead?')

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info('test ended')

