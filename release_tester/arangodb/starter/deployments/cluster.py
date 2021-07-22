#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

from tools.timestamp import timestamp
from tools.interact import prompt_user
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner, PunnerProperties
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress


class Cluster(Runner):
    """ this launches a cluster setup """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, abort_on_error, installer_set,
                 selenium, selenium_driver_args,
                 testrun_name: str):
        super().__init__(runner_type, abort_on_error, installer_set,
                         PunnerProperties('CLUSTER', 400, 600, True),
                         selenium, selenium_driver_args,
                         testrun_name)
        #self.basecfg.frontends = []
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.create_test_collection = ""

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
                               InstanceType.AGENT,
                               InstanceType.COORDINATOR,
                               InstanceType.DBSERVER
                           ],
                           moreopts=[]))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node2',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9628,
                           expect_instances=[
                               InstanceType.AGENT,
                               InstanceType.COORDINATOR,
                               InstanceType.DBSERVER
                           ],
                           moreopts=['--starter.join', '127.0.0.1:9528']))
        self.starter_instances.append(
            StarterManager(self.basecfg,
                           self.basedir, 'node3',
                           mode='cluster',
                           jwtStr=self.jwtdatastr,
                           port=9728,
                           expect_instances=[
                               InstanceType.AGENT,
                               InstanceType.COORDINATOR,
                               InstanceType.DBSERVER
                           ],
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
        count = 0
        for node in self.starter_instances:
            node.set_passvoid('cluster', count == 0)
            count += 1
        self.passvoid = 'cluster'

    def finish_setup_impl(self):
        self.makedata_instances = self.starter_instances[:]
        self.set_frontend_instances()

    def test_setup_impl(self):
        pass

    def wait_for_restore_impl(self, backup_starter):
        for starter in self.starter_instances:
            for dbserver in starter.get_dbservers():
                dbserver.detect_restore_restart()

    def upgrade_arangod_version_impl(self):
        bench_instances = []
        if self.cfg.stress_upgrade:
            bench_instances.append(self.starter_instances[0].launch_arangobench(
                'cluster_upgrade_scenario_1'))
            bench_instances.append(self.starter_instances[1].launch_arangobench(
                'cluster_upgrade_scenario_2'))
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)

        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        if self.selenium:
            self.selenium.upgrade_deployment(self.cfg, self.new_cfg, timeout=30) # * 5s
        self.starter_instances[1].wait_for_upgrade(300)
        if self.cfg.stress_upgrade:
            bench_instances[0].wait()
            bench_instances[1].wait()

    def jam_attempt_impl(self):
        agency_leader = self.agency_get_leader()
        terminate_instance = 2
        if self.starter_instances[terminate_instance].have_this_instance(agency_leader):
            print("Cluster instance 2 has the agency leader; killing 1 instead")
            terminate_instance = 1

        logging.info("stopping instance %d" % terminate_instance)

        self.starter_instances[terminate_instance].terminate_instance()
        self.set_frontend_instances()
        if not self.starter_instances[0].arangosh.check_test_data(
                "Cluster one node missing", True)[0]:
            roise Exception("check data failed")

        prompt_user(self.basecfg, "instance stopped")
        if self.selenium:
            self.selenium.jam_step_1(self.new_cfg if self.new_cfg else self.cfg)

        # respawn instance, and get its state fixed
        self.starter_instances[terminate_instance].respawn_instance()
        self.set_frontend_instances()
        while not self.starter_instances[terminate_instance].is_instance_up():
            progress('.')
            time.sleep(1)
        print()
        self.starter_instances[terminate_instance].detect_instances()
        self.starter_instances[terminate_instance].detect_instance_pids()
        self.starter_instances[terminate_instance].detect_instance_pids_still_alive()
        self.set_frontend_instances()

        logging.info('jamming: Starting instance without jwt')
        dead_instance = StarterManager(
            self.basecfg,
            Path('CLUSTER'), 'nodeX',
            mode='cluster',
            jwtStr=None,
            expect_instances=[
                InstanceType.AGENT,
                InstanceType.COORDINATOR,
                InstanceType.DBSERVER
            ],
            moreopts=['--starter.join', '127.0.0.1:9528'])
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

        prompt_user(self.basecfg, "cluster should be up")
        if self.selenium:
            self.selenium.jam_step_2(self.new_cfg if self.new_cfg else self.cfg)

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info('test ended')

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
