#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path
import semver

from reporting.reporting_utils import step
from tools.timestamp import timestamp
from tools.interact import prompt_user
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner, RunnerProperties
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

arangoversions = {
    "370": semver.VersionInfo.parse("3.7.0"),
}
class Cluster(Runner):
    """this launches a cluster setup"""

    # pylint: disable=R0913 disable=R0902
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        testrun_name: str,
        ssl: bool,
        use_auto_certs: bool,
    ):
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("CLUSTER", 400, 600, True, ssl, use_auto_certs),
            selenium,
            selenium_driver_args,
            testrun_name,
        )
        # self.basecfg.frontends = []
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.create_test_collection = ""
        self.min_replication_factor = 2

    def starter_prepare_env_impl(self):
        self.create_test_collection = (
            """
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""",
            "create test collection",
        )
        node1_opts = []
        node2_opts = ["--starter.join", "127.0.0.1:9528"]
        node3_opts = ["--starter.join", "127.0.0.1:9528"]
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
            node1_tls_keyfile = self.cert_dir / Path("node1") / "tls.keyfile"
            node2_tls_keyfile = self.cert_dir / Path("node2") / "tls.keyfile"
            node3_tls_keyfile = self.cert_dir / Path("node3") / "tls.keyfile"

            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(node1_tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(node2_tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(node3_tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            node1_opts.append(f"--ssl.keyfile={node1_tls_keyfile}")
            node2_opts.append(f"--ssl.keyfile={node2_tls_keyfile}")
            node3_opts.append(f"--ssl.keyfile={node2_tls_keyfile}")

        def add_starter(name, port, opts):
            self.starter_instances.append(
                StarterManager(
                    self.basecfg,
                    self.basedir,
                    name,
                    mode="cluster",
                    jwtStr=self.jwtdatastr,
                    port=port,
                    expect_instances=[
                        InstanceType.AGENT,
                        InstanceType.COORDINATOR,
                        InstanceType.DBSERVER,
                    ],
                    moreopts=opts,
                )
            )

        add_starter("node1", 9528, node1_opts)
        add_starter("node2", 9628, node2_opts)
        add_starter("node3", 9728, node3_opts)

        for instance in self.starter_instances:
            instance.is_leader = True

    def starter_run_impl(self):
        lh.subsection("instance setup")
        for manager in self.starter_instances:
            logging.info("Spawning instance")
            manager.run_starter()

        logging.info("waiting for the starters to become alive")
        not_started = self.starter_instances[:]  # This is a explicit copy
        while not_started:
            logging.debug("waiting for mananger with logfile:" + str(not_started[-1].log_file))
            if not_started[-1].is_instance_up():
                not_started.pop()
            progress(".")
            time.sleep(1)

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.detect_instance_pids()
            # self.basecfg.add_frontend('http', self.basecfg.publicip, str(node.get_frontend_port()))
        logging.info("instances are ready")
        count = 0
        for node in self.starter_instances:
            node.set_passvoid("cluster", count == 0)
            count += 1
        self.passvoid = "cluster"

    def finish_setup_impl(self):
        self.makedata_instances = self.starter_instances[:]
        self.set_frontend_instances()

    def test_setup_impl(self):
        self.wikidata_import_impl()
        self.execute_views_tests_impl()
        pass

    def wait_for_restore_impl(self, backup_starter):
        for starter in self.starter_instances:
            for dbserver in starter.get_dbservers():
                dbserver.detect_restore_restart()

    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        self.agency_set_debug_logging()  # TODO: remove debug logging
        bench_instances = []
        if self.cfg.stress_upgrade:
            bench_instances.append(self.starter_instances[0].launch_arangobench("cluster_upgrade_scenario_1"))
            bench_instances.append(self.starter_instances[1].launch_arangobench("cluster_upgrade_scenario_2"))
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)

        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        if self.selenium:
            self.selenium.upgrade_deployment(self.cfg, self.new_cfg, timeout=30)  # * 5s
        self.starter_instances[1].wait_for_upgrade(300)
        if self.cfg.stress_upgrade:
            bench_instances[0].wait()
            bench_instances[1].wait()
        for node in self.starter_instances:
            node.detect_instance_pids()

    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg, False)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        # fmt: off
        self.progress(True, "step 2 - upgrade agents")
        for node in self.starter_instances:
            node.upgrade_instances(
                [
                    InstanceType.AGENT
                ], [
                    '--database.auto-upgrade', 'true',
                    '--log.foreground-tty', 'true'
                ],
                # mitigate 3.6x agency shutdown issues:
                self.cfg.version >= arangoversions['370'])
        self.progress(True, "step 3 - upgrade db-servers")
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.DBSERVER
            ], ['--database.auto-upgrade', 'true',
                '--log.level', 'startup=trace', # TODO: remove me again.
                '--log.foreground-tty', 'true'])
        self.progress(True, "step 4 - coordinator upgrade")
        # now the new cluster is running. we will now run the coordinator upgrades
        for node in self.starter_instances:
            logging.info("upgrading coordinator instances\n" + str(node))
            node.upgrade_instances([
                InstanceType.COORDINATOR
            ], [
                '--database.auto-upgrade', 'true',
                '--javascript.copy-installation', 'true',
                '--server.rest-server', 'false',
            ])
        # fmt: on
        self.progress(True, "step 5 restart the full cluster ")
        for node in self.starter_instances:
            node.respawn_instance()
        self.progress(True, "step 6 wait for the cluster to be up")
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()

        # now the upgrade should be done.
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()
            node.probe_leader()
        self.set_frontend_instances()
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)

        if self.selenium:
            self.selenium.upgrade_deployment(self.cfg, self.new_cfg, timeout=30)  # * 5s

    @step
    def jam_attempt_impl(self):
        # this is simply to slow to be worth wile:
        # collections = self.get_collection_list()
        agency_leader = self.agency_get_leader()
        terminate_instance = 2
        survive_instance = 1
        if self.starter_instances[terminate_instance].have_this_instance(agency_leader):
            print("Cluster instance 2 has the agency leader; killing 1 instead")
            terminate_instance = 1
            survive_instance = 2

        logging.info("stopping instance %d" % terminate_instance)
        uuid = self.starter_instances[terminate_instance].get_dbservers()[0].get_uuid()
        self.starter_instances[terminate_instance].terminate_instance()
        self.set_frontend_instances()

        prompt_user(self.basecfg, "instance stopped")
        if self.selenium:
            self.selenium.jam_step_1(self.new_cfg if self.new_cfg else self.cfg)

        ret = self.starter_instances[0].arangosh.check_test_data(
            "Cluster one node missing", True, ["--disabledDbserverUUID", uuid]
        )
        if not ret[0]:
            raise Exception("check data failed " + ret[1])

        ret = self.starter_instances[survive_instance].arangosh.check_test_data(
            "Cluster one node missing", True, ["--disabledDbserverUUID", uuid]
        )
        if not ret[0]:
            raise Exception("check data failed " + ret[1])

        # respawn instance, and get its state fixed
        self.starter_instances[terminate_instance].respawn_instance()
        self.set_frontend_instances()
        while not self.starter_instances[terminate_instance].is_instance_up():
            progress(".")
            time.sleep(1)
        print()
        self.starter_instances[terminate_instance].detect_instances()
        self.starter_instances[terminate_instance].detect_instance_pids()
        self.starter_instances[terminate_instance].detect_instance_pids_still_alive()
        self.set_frontend_instances()

        logging.info("jamming: Starting instance without jwt")
        dead_instance = StarterManager(
            self.basecfg,
            Path("CLUSTER"),
            "nodeX",
            mode="cluster",
            jwtStr=None,
            expect_instances=[
                InstanceType.AGENT,
                InstanceType.COORDINATOR,
                InstanceType.DBSERVER,
            ],
            moreopts=["--starter.join", "127.0.0.1:9528"],
        )
        dead_instance.run_starter()

        i = 0
        while True:
            logging.info(". %d", i)
            if not dead_instance.is_instance_running():
                break
            if i > 40:
                logging.info("Giving up wating for the starter to exit")
                raise Exception("non-jwt-ed starter won't exit")
            i += 1
            time.sleep(10)
        logging.info(str(dead_instance.instance.wait(timeout=320)))
        logging.info("dead instance is dead?")

        prompt_user(self.basecfg, "cluster should be up")
        if self.selenium:
            self.selenium.jam_step_2(self.new_cfg if self.new_cfg else self.cfg)

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info("test ended")

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
