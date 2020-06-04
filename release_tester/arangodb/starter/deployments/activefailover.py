#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from pathlib import Path
import time
import logging
import sys
import requests
from tools.interact import prompt_user
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh


class ActiveFailover(Runner):
    """ This launches an active failover setup """
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst):
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst, 'AFO')
        self.starter_instances = []
        self.follower_nodes = None
        self.leader = None
        self.new_leader = None

    def starter_prepare_env_impl(self):
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

    def starter_run_impl(self):
        logging.info("Spawning starter instances")
        for node in self.starter_instances:
            logging.info("Spawning starter instance in: " + str(node.basedir))
            node.run_starter()

        logging.info("waiting for the starters to become alive")
        while (not self.starter_instances[0].is_instance_up()
               and not self.starter_instances[1].is_instance_up()
               and not self.starter_instances[1].is_instance_up()):
            sys.stdout.write(".")
            time.sleep(1)

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.active_failover_detect_hosts()

    def finish_setup_impl(self):
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

        #add data to leader
        self.makedata_instances.append(self.leader)

        logging.info("active failover setup finished successfully")

    def test_setup_impl(self):
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


    def upgrade_arangod_version_impl(self):
        """ upgrade this installation """
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()
        self.starter_instances[1].command_upgrade()
        self.starter_instances[1].wait_for_upgrade()

    def jam_attempt_impl(self):
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
                print('.', end='')
            time.sleep(1)
        print()

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
        prompt_user(self.basecfg)
        self.leader.respawn_instance()

        logging.info("waiting for old leader to show up as follower")
        while not self.leader.active_failover_detect_host_now_follower():
            print('.', end='')
            time.sleep(1)
        print()

        logging.info("FIXME -- ???? Now is follower") ##FIXME - Who is follower?

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

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()

        logging.info('test ended')
