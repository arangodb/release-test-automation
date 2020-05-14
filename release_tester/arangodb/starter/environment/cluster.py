#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
from pathlib import Path

from tools.timestamp import timestamp
from tools.quote_user import quote_user, end_test
from arangodb.starter.manager import StarterManager
from arangodb.starter.environment.runner import Runner


class Cluster(Runner):
    """ this launches a cluster setup """
    def __init__(self, cfg):
        logging.info("x"*80)
        logging.info("xx           cluster test      ")
        logging.info("x"*80)
        self.success = True
        self.create_test_collection = ("""
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""", "create test collection")
        self.basecfg = cfg
        self.basecfg.frontends = []
        self.basedir = Path('CLUSTER')
        self.cleanup()
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())

        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node1',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node2',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=['--starter.join', '127.0.0.1']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node3',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           moreopts=['--starter.join', '127.0.0.1']))

    def setup(self):
        for node in self.starter_instances:
            logging.info("Spawning instance")
            node.run_starter()

        logging.info("waiting for the starters to become alive")
        not_started = self.starter_instances[:] #This is a explicit copy
        while not_started:
            if not_started[-1].is_instance_up():
                not_started.pop()
                logging.debug("waiting for mananger with logfile:" + not_started[1].log_file)
            print('.', end='')
            sys.stdout.flush()
            time.sleep(1)

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_logfiles()
            node.detect_instance_pids()
            self.basecfg.add_frontend('http',
                                      self.basecfg.publicip,
                                      str(node.get_frontend_port()))

    def run(self):
        logging.info("instances are ready")
        quote_user(self.basecfg)
        #  TODO self.create_test_collection
        logging.info("stopping instance 2")
        self.starter_instances[2].terminate_instance()
        end_test(self.basecfg, "instance stopped")
        # respawn instance, and get its state fixed
        self.starter_instances[2].respawn_instance()
        while not self.starter_instances[2].is_instance_up():
            logging.info('.')
            time.sleep(1)
        self.starter_instances[2].detect_logfiles()
        self.starter_instances[2].detect_instance_pids()
        self.starter_instances[2].detect_instance_pids_still_alive()

    def upgrade(self, newInstallCfg):
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(newInstallCfg)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()
        self.starter_instances[1].command_upgrade()
        self.starter_instances[1].wait_for_upgrade()

    def post_setup(self):
        pass

    def jam_attempt(self):
        logging.info('Starting instance without jwt')
        dead_instance = StarterManager(
            self.basecfg,
            Path('CLUSTER') / 'nodeX',
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

    def shutdown(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info('test ended')
