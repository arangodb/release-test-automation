#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path
import copy
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

more_nodes_supported_starter = [
    [ semver.VersionInfo.parse("3.11.8-99"),semver.VersionInfo.parse("3.11.99")],
    [ semver.VersionInfo.parse("3.11.99"),semver.VersionInfo.parse("3.12.99")],
]

class Cluster(Runner):
    """this launches a cluster setup"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        selenium_include_suites,
        testrun_name: str,
        ssl: bool,
        replication2: bool,
        use_auto_certs: bool,
        force_one_shard: bool,
        create_oneshard_db: bool,
        cluster_nodes: int,
    ):
        name = "CLUSTER" if not force_one_shard else "FORCED_ONESHARD_CLUSTER"
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties(
                name, 400, 600, True, ssl, replication2, use_auto_certs, force_one_shard, create_oneshard_db, 6
            ),
            selenium,
            selenium_driver_args,
            selenium_include_suites,
            testrun_name,
        )
        self.force_one_shard = force_one_shard
        self.create_oneshard_db = create_oneshard_db
        # self.cfg.frontends = []
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.create_test_collection = ""
        self.min_replication_factor = 2
        self.cluster_nodes = cluster_nodes
        if cluster_nodes > 3:
            ver_found = 0
            versions = self.get_versions_concerned()
            for ver_pair in more_nodes_supported_starter:
                for version in versions:
                    if ver_pair[0] <= version < ver_pair[1]:
                        ver_found += 1
            if ver_found < len(versions):
                print("One deployment doesn't support starters with more nodes!")
                self.cluster_nodes = 3

    def starter_prepare_env_impl(self, sm=None):
        # pylint: disable=invalid-name
        def add_starter(name, port, opts, sm, hasAgency):
            agencyInstance = []
            if hasAgency:
                agencyInstance = [InstanceType.AGENT]
            if sm is None:
                sm = StarterManager
            self.starter_instances.append(
                sm(
                    self.cfg,
                    self.basedir,
                    name,
                    mode="cluster",
                    jwt_str=self.jwtdatastr,
                    port=port,
                    expect_instances=agencyInstance
                    + [
                        InstanceType.COORDINATOR,
                        InstanceType.DBSERVER,
                    ],
                    moreopts=opts,
                )
            )

        self.create_test_collection = (
            "create test collection",
            """
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""",
        )
        common_opts = []
        if self.replication2:
            common_opts += [
                "--dbservers.database.default-replication-version=2",
                "--coordinators.database.default-replication-version=2",
                "--args.all.log.level=replication2=debug",
                "--args.all.log.level=rep-state=debug",
            ]
        if self.force_one_shard:
            common_opts += [
                "--coordinators.cluster.force-one-shard=true",
                "--dbservers.cluster.force-one-shard=true",
                "--args.coordinators.log-level=requests=trace",
                "--args.coordinators.argument=--log-file=@ARANGODB_SERVER_DIR@/request.log",
            ]
        else:
            common_opts += ["--args.all.cluster.default-replication-factor=2"]
        node_opts = []
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
        port = 9528
        count = 0
        for this_node in list(range(1, self.cluster_nodes + 1)):
            node = []
            node_opts.append(node)
            if this_node != 1:
                node += ["--starter.join", "127.0.0.1:9528"]
            if self.cfg.ssl and not self.cfg.use_auto_certs:
                node_tls_keyfile = self.cert_dir / Path(f"node{this_node}") / "tls.keyfile"
                self.generate_keyfile(node_tls_keyfile)
                node.append(f"--ssl.keyfile={node_tls_keyfile}")
            add_starter(f"node{this_node}", port, node + common_opts, sm, count < 3)
            port += 100
            count += 1
        self.backup_instance_count = count
        for instance in self.starter_instances:
            instance.is_leader = True

    def starter_run_impl(self):
        lh.subsection("instance setup")
        for manager in self.starter_instances:
            logging.info("Spawning instance")
            manager.run_starter()

        logging.info("waiting for the starters to become alive")
        not_started = self.starter_instances[:]  # This is a explicit copy
        count = 0
        while not_started:
            logging.debug("waiting for mananger with logfile:" + str(not_started[-1].log_file))
            if not_started[-1].is_instance_up():
                not_started.pop()
            progress(".")
            time.sleep(1)
            count += 1
            if count > 120:
                raise Exception("Cluster installation didn't come up in two minutes!")

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.detect_instance_pids()
            # self.cfg.add_frontend('http', self.cfg.publicip, str(node.get_frontend_port()))

        logging.info("instances are ready - JWT: " + self.starter_instances[0].get_jwt_header())
        count = 0
        for node in self.starter_instances:
            node.set_passvoid("cluster", count == 0)
            count += 1
        self.passvoid = "cluster"

    def finish_setup_impl(self):
        self.makedata_instances = self.starter_instances[:]
        self.set_frontend_instances()

    def _check_for_shards_in_sync(self):
        """wait for all shards to be in sync"""
        lh.subsubsection("wait for all shards to be in sync - Jamming")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
        )
        if not retval:
            raise Exception("Failed to ensure the cluster is in sync: %s" % (retval))
        print("all in sync.")

    def test_setup_impl(self):
        if self.selenium:
            self.selenium.test_setup()

    def after_makedata_check(self):
        lh.subsubsection("wait for all shards to be in sync - test setup")
        self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
        )

    def wait_for_restore_impl(self, backup_starter):
        for starter in self.starter_instances:
            for dbserver in starter.get_dbservers():
                dbserver.detect_restore_restart()
        self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
        )

    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        # self.agency_set_debug_logging()
        bench_instances = []
        if self.cfg.stress_upgrade:
            bench_instances.append(self.starter_instances[0].launch_arangobench("cluster_upgrade_scenario_1"))
            bench_instances.append(self.starter_instances[1].launch_arangobench("cluster_upgrade_scenario_2"))
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg)

        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        if self.selenium:
            self.selenium.test_wait_for_upgrade()  # * 5s
        self.starter_instances[1].wait_for_upgrade(300)
        if self.cfg.stress_upgrade:
            bench_instances[0].wait()
            bench_instances[1].wait()
        for node in self.starter_instances:
            node.detect_instance_pids()

    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        lh.subsubsection("wait for all shards to be in sync - Manual upgrade")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
        )
        if not retval:
            raise Exception("Failed to ensure the cluster is in sync: %s" % (retval))
        print("all in sync.")
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg, False)
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
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        for node in self.starter_instances:
            node.respawn_instance(version)
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
            self.selenium.test_wait_for_upgrade()  # * 5s

    def downgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        lh.subsubsection("wait for all shards to be in sync - downgrade")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
        )
        if not retval:
            raise Exception("Failed to ensure the cluster is in sync: %s" % (retval))
        print("all in sync.")
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg, False)
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
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        for node in self.starter_instances:
            node.respawn_instance(version)
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
            self.selenium.test_wait_for_upgrade()  # * 5s

    def _jam_stop_one_db_server(self):
        agency_leader = self.agency.get_leader()
        terminate_instance = 2
        survive_instance = 1
        if self.starter_instances[terminate_instance].have_this_instance(agency_leader):
            print("Cluster instance 2 has the agency leader; killing 1 instead")
            terminate_instance = 1
            survive_instance = 2

        logging.info("stopping instance %d" % terminate_instance)
        uuid = self.starter_instances[terminate_instance].get_dbservers()[0].get_uuid()
        self.starter_instances[terminate_instance].terminate_instance(keep_instances=True)
        logging.info("relaunching agent!")
        self.starter_instances[terminate_instance].manually_launch_instances([InstanceType.AGENT], [], False, False)

        if self.replication2:
            self.remove_server_from_agency(uuid)

        self.set_frontend_instances()

        prompt_user(self.cfg, "instance stopped")
        if self.selenium:
            self.selenium.jam_step_1()

        for starter_instance in [self.starter_instances[0], self.starter_instances[survive_instance]]:
            for db_name, oneshard, count_offset in self.makedata_databases():
                ret = starter_instance.arangosh.check_test_data(
                    "Cluster one node missing",
                    True,
                    ["--disabledDbserverUUID", uuid, "--countOffset", str(count_offset)],
                    oneshard,
                    db_name,
                )
                if not ret[0]:
                    raise Exception("check data failed in database %s :\n" % db_name + ret[1])

        self.starter_instances[terminate_instance].kill_specific_instance([InstanceType.AGENT])

        # respawn instance, and get its state fixed
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        self.starter_instances[terminate_instance].respawn_instance(version)
        self.set_frontend_instances()
        counter = 300
        while not self.starter_instances[terminate_instance].is_instance_up():
            if counter <= 0:
                raise Exception("Instance did not respawn in 5 minutes!")
            progress(".")
            time.sleep(1)
            counter -= 1
        self.starter_instances[terminate_instance].detect_instances()
        self.starter_instances[terminate_instance].detect_instance_pids()
        self.starter_instances[terminate_instance].detect_instance_pids_still_alive()
        self.set_frontend_instances()

    def _jam_launch_unauthicanted_starter(self):
        moreopts = ["--starter.join", "127.0.0.1:9528"]
        curr_cfg = {}
        if self.new_cfg is not None:
            curr_cfg = copy.deepcopy(self.new_cfg)
        else:
            curr_cfg = copy.deepcopy(self.cfg)

        if curr_cfg.ssl and not curr_cfg.use_auto_certs:
            keyfile = self.cert_dir / Path("nodeX") / "tls.keyfile"
            self.generate_keyfile(keyfile)
            moreopts.append(f"--ssl.keyfile={keyfile}")
        dead_instance = StarterManager(
            curr_cfg,
            Path("CLUSTER"),
            "nodeX",
            mode="cluster",
            jwt_str=None,
            expect_instances=[
                InstanceType.AGENT,
                InstanceType.COORDINATOR,
                InstanceType.DBSERVER,
            ],
            moreopts=moreopts,
        )
        dead_instance.run_starter(expect_to_fail=True)

        i = 0
        while True:
            logging.info(". %d", i)
            if not dead_instance.is_instance_running():
                dead_instance.check_that_starter_log_contains("Unauthorized. Wrong credentials.")
                break
            if i > 40:
                logging.info("Giving up wating for the starter to exit")
                raise Exception("non-jwt-ed starter won't exit")
            i += 1
            time.sleep(10)
        logging.info(str(dead_instance.instance.wait(timeout=320)))
        logging.info("dead instance is dead?")
        prompt_user(curr_cfg, "cluster should be up")

    @step
    def jam_attempt_impl(self):
        # pylint: disable=too-many-statements disable=too-many-branches
        # this is simply to slow to be worth wile:
        # collections = self.get_collection_list()
        self._check_for_shards_in_sync()
        self._jam_stop_one_db_server()

        logging.info("jamming: Starting instance without jwt")
        self._jam_launch_unauthicanted_starter()
        if self.selenium:
            self.selenium.jam_step_2()

    def shutdown_impl(self):
        ret = False
        for node in self.starter_instances:
            ret = ret or node.terminate_instance()
        logging.info("test ended")
        return ret

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        self._check_for_shards_in_sync()

    def before_backup_create_impl(self):
        pass

    def after_backup_create_impl(self):
        pass

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.starter_instances[0].arango_importer,
            self.starter_instances[0].arango_restore,
            [x for x in self.starter_instances[0].all_instances if x.instance_type == InstanceType.COORDINATOR][0],
            self.new_cfg,
        )

    def generate_keyfile(self, keyfile):
        """generate the ssl certificate file"""
        self.cert_op(
            [
                "tls",
                "keyfile",
                "--cacert=" + str(self.certificate_auth["cert"]),
                "--cakey=" + str(self.certificate_auth["key"]),
                "--keyfile=" + str(keyfile),
                "--host=" + self.cfg.publicip,
                "--host=localhost",
            ]
        )
