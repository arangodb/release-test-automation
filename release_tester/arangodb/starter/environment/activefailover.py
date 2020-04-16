#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from pathlib import Path
import time
import logging
import requests
from tools.quote_user import quote_user
from arangodb.starter.manager import StarterManager
from arangodb.starter.environment.runner import Runner

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class ActiveFailover(Runner):
    """ This launches an active failover setup """
    def __init__(self, cfg):
        logging.info("x"*80)
        logging.info("xx           Active Failover Test      ")
        logging.info("x"*80)
        self.success = True
        self.basecfg = cfg
        self.basedir = Path('AFO')
        self.cleanup()
        self.starter_instances = []
        self.follower_nodes = None
        self.leader = None
        self.new_leader = None
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node1',
                           mode='activefailover',
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node2',
                           mode='activefailover',
                           moreopts=['--starter.join', '127.0.0.1']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir / 'node3',
                           mode='activefailover',
                           moreopts=['--starter.join', '127.0.0.1']))

    def setup(self):
        for node in self.starter_instances:
            logging.info("Spawning instance")
            node.run_starter()
        logging.info("waiting for the starters to become alive")
        while (not self.starter_instances[0].is_instance_up()
               and not self.starter_instances[1].is_instance_up()
               and not self.starter_instances[1].is_instance_up()):
            logging.info('.')
            time.sleep(1)
        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_logfiles()
            node.active_failover_detect_hosts()
        logging.info("instances are ready, detecting leader")
        self.follower_nodes = []
        while self.leader is None:
            for node in self.starter_instances:
                if node.detect_leader():
                    self.leader = node
                    break
        for node in self.starter_instances:
            node.detect_instance_pids()
            if not node.is_leader:
                self.follower_nodes.append(node)
        logging.info("system ready")

    def run(self):
        logging.info("starting test")
        self.success = True
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.leader.get_frontend_port())

        reply = requests.get(url)
        logging.info(str(reply))
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.follower_nodes[0].get_frontend_port())
        reply = requests.get(url)
        logging.info(str(reply))
        logging.info(reply.text)
        if reply.status_code != 503:
            self.success = False
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.follower_nodes[1].get_frontend_port())
        reply = requests.get(url)
        logging.info(str(reply))
        logging.info(reply.text)
        if reply.status_code != 503:
            self.success = False
        logging.info("success" if self.success else "fail")
        logging.info('leader can be reached at: http://%s:%s',
                     self.basecfg.publicip,
                     self.leader.get_frontend_port())

    def post_setup(self):
        pass

    def jam_attempt(self):
        self.leader.terminate_instance()
        logging.info("waiting for new leader...")
        self.new_leader = None
        while self.new_leader is None:
            for node in self.follower_nodes:
                node.detect_leader()
                if node.is_leader:
                    logging.info('have a new leader: %s', str(node.arguments))
                    self.new_leader = node
                    break
                logging.info('.')
            time.sleep(1)
        logging.info(str(self.new_leader))
        url = 'http://{host}:{port}{uri}'.format(
            host=self.basecfg.localhost,
            port=self.new_leader.get_frontend_port(),
            uri='/_db/_system/_admin/aardvark/index.html#replication')
        reply = requests.get(url)
        logging.info(str(reply))
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False
        self.basecfg.add_frontend('http',
                                  self.basecfg.publicip,
                                  str(self.leader.get_frontend_port()))
        quote_user(self.basecfg)
        self.leader.respawn_instance()

        logging.info("waiting for old leader to show up as follower")
        while not self.leader.active_failover_detect_host_now_follower():
            logging.info('.')
            time.sleep(1)
        logging.info("Now is follower")
        url = 'http://{host}:{port}'.format(
            host=self.basecfg.localhost,
            port=self.leader.get_frontend_port())
        reply = requests.get(url)
        logging.info(str(reply))
        logging.info(str(reply.text))
        if reply.status_code != 503:
            self.success = False
        logging.info("state of this test is: %s",
                     "Success" if self.success else "Failed")

    def shutdown(self):
        for node in self.starter_instances:
            node.terminate_instance()

        logging.info('test ended')
