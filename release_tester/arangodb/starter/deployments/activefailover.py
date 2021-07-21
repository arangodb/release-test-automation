#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
import requests
from requests.auth import HTTPBasicAuth

from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner, PunnerProperties

from tools.asciiprint import print_progress as progress
from tools.interact import prompt_user


class ActiveFailover(Runner):
    """ This launches an active failover setup """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, abort_on_error, installer_set,
                 selenium, selenium_driver_args,
                 testrun_name: str):
        super().__init__(runner_type, abort_on_error, installer_set,
                         PunnerProperties('ActiveFailOver', 500, 600, True),
                         selenium, selenium_driver_args,
                         testrun_name)
        self.starter_instances = []
        self.follower_nodes = None
        self.leader = None
        self.first_leader = None
        self.new_leader = None
        self.success = True
        self.backup_instance_count = 1

    def starter_prepare_env_impl(self):
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node1',
                           mode='activefailover',
                           port=9528,
                           expect_instances=[
                               InstanceType.AGENT,
                               InstanceType.RESILIENT_SINGLE
                           ],
                           jwtStr="afo",
                           moreopts=['--all.log.level=replication=debug']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node2',
                           mode='activefailover',
                           port=9628,
                           expect_instances=[
                               InstanceType.AGENT,
                               InstanceType.RESILIENT_SINGLE
                           ],
                           jwtStr="afo",
                           moreopts=[
                               '--starter.join',
                               '127.0.0.1:9528',
                               '--all.log.level=replication=debug'
                           ]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node3',
                           mode='activefailover',
                           port=9728,
                           expect_instances=[
                               InstanceType.AGENT,
                               InstanceType.RESILIENT_SINGLE
                           ],
                           jwtStr="afo",
                           moreopts=[
                               '--starter.join',
                               '127.0.0.1:9528',
                               '--all.log.level=replication=debug'
                           ]))

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
                    self.first_leader = node

        for node in self.starter_instances:
            node.detect_instance_pids()
            if not node.is_leader:
                self.follower_nodes.append(node)
            node.set_passvoid('leader', node.is_leader)


        #add data to leader
        self.makedata_instances.append(self.leader)

        logging.info('leader can be reached at: %s',
                     self.leader.get_frontend().get_public_url(''))
        self.set_frontend_instances()
        logging.info("active failover setup finished successfully")

    def test_setup_impl(self):
        self.success = True

        url = self.leader.get_frontend().get_local_url('')
        reply = requests.get(url, auth=HTTPBasicAuth('root', self.leader.passvoid))
        logging.info(str(reply))
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False

        url = self.follower_nodes[0].get_frontend().get_local_url('')
        reply = requests.get(url, auth=HTTPBasicAuth('root', self.leader.passvoid))
        logging.info(str(reply))
        logging.info(reply.text)
        if reply.status_code != 503:
            self.success = False

        url = self.follower_nodes[1].get_frontend().get_local_url('')
        reply = requests.get(url, auth=HTTPBasicAuth('root', self.leader.passvoid))
        logging.info(str(reply))
        logging.info(reply.text)
        if reply.status_code != 503:
            self.success = False
        logging.info("success" if self.success else "fail")
        logging.info('leader can be reached at: %s',
                     self.leader.get_frontend().get_public_url(''))
        self.follower_nodes[0].arangosh.check_test_data(
            "checking active failover follower node", [
                "--readOnly", "true"
            ],
            True)

    def wait_for_restore_impl(self, backup_starter):
        backup_starter.wait_for_restore()
        self.leader = None
        for node in self.starter_instances:
            if node.probe_leader():
                self.leader = node
        if self.leader is None:
            raise Exception("wasn't able to detect the leader after restoring the backup!")

    def upgrade_arangod_version_impl(self):
        """ upgrade this installation """
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()
        self.starter_instances[1].command_upgrade()
        self.starter_instances[1].wait_for_upgrade(180)
        for node in self.starter_instances:
            node.detect_instance_pids()
        self.print_all_instances_table()
        if self.selenium:
            self.selenium.web.refresh() # version doesn't upgrade if we don't do this...
            self.selenium.check_old(self.new_cfg,
                                    expect_follower_count=2, retry_count=10)

    def jam_attempt_impl(self):
        # pylint: disable=R0915
        agency_leader = self.agency_get_leader()
        if self.first_leader.have_this_instance(agency_leader):
            print("AFO-Leader and agency leader are attached by the same starter!")
            self.agency_trigger_leader_relection(agency_leader)

        self.first_leader.terminate_instance()
        logging.info("waiting for new leader...")
        self.new_leader = None

        count = 0
        while self.new_leader is None:
            for node in self.follower_nodes:
                node.detect_leader()
                if node.is_leader:
                    logging.info('have a new leader: %s', str(node.arguments))
                    self.new_leader = node
                    self.leader = node
                    break
                progress('.')
            time.sleep(1)
            if count > 360:
                #self.progress(False, "Timeout waiting for new leader - crashing!")
                #for node in self.starter_instances:
                #    node.crash_instances()
                raise TimeoutError("Timeout waiting for new leader!")
            count += 1

        print()
        self.new_leader.arangosh.check_test_data("checking active failover new leader node")

        logging.info("\n" + str(self.new_leader))
        url = '{host}/_db/_system/_admin/aardvark/index.html#replication'.format(
            host=self.new_leader.get_frontend().get_local_url(''))
        reply = requests.get(url, auth=HTTPBasicAuth('root', self.leader.passvoid))
        logging.info(str(reply))
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False
        self.set_frontend_instances()

        if self.selenium:
            self.selenium.connect_server(self.leader.get_frontends(), '_system',
                                         self.new_cfg if self.new_cfg else self.cfg)
            cfg = self.new_cfg if self.new_cfg else self.cfg
            self.selenium.check_old(cfg=cfg, expect_follower_count=1, retry_count=10)

        prompt_user(self.basecfg,
                    '''The leader failover has happened.
please revalidate the UI states on the new leader; you should see *one* follower.''')
        self.first_leader.respawn_instance()
        self.first_leader.detect_instances()
        logging.info("waiting for old leader to show up as follower")
        while not self.first_leader.active_failover_detect_host_now_follower():
            progress('.')
            time.sleep(1)
        print()

        url = self.first_leader.get_frontend().get_local_url('')

        reply = requests.get(url, auth=HTTPBasicAuth('root', self.leader.passvoid))
        logging.info(str(reply))
        logging.info(str(reply.text))

        if reply.status_code != 503:
            self.success = False

        prompt_user(self.basecfg,
                    'The old leader has been respawned as follower (%s),'
                    ' so there should be two followers again.'
                    % self.first_leader.get_frontend().get_public_url('root@') )

        logging.info("state of this test is: %s",
                     "Success" if self.success else "Failed")
        if self.selenium:
            cfg = self.new_cfg if self.new_cfg else self.cfg
            self.selenium.check_old(cfg=cfg, expect_follower_count=2, retry_count=10)

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()

        logging.info('test ended')

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
