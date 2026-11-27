#!/usr/bin/env python
""" launch and manage an RBAC-enabled arango cluster deployment using the starter"""
import copy
import json
import logging
from pathlib import Path
import re
import time
import os

import semver

from reporting.reporting_utils import step
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress
from tools.timestamp import timestamp
from tools.interact import prompt_user

from arangodb.instance import InstanceType
from arangodb.installers import RunProperties
from arangodb.installers.depvar import RunnerProperties
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner

from api_tests.test_suites.api_test_suite import APITestSuite

from operator_integration_tests.helpers.rbac_helper import RBAC_SERVICE_GATEWAY
from operator_integration_tests.helpers.rbac_helper import RBACHelper


arangoversions = {
    "370": semver.VersionInfo.parse("3.7.0"),
    "3126": semver.VersionInfo.parse("3.12.6"),
}

more_nodes_supported_starter = [
    [semver.VersionInfo.parse("3.11.8-99"), semver.VersionInfo.parse("3.11.99")],
    [semver.VersionInfo.parse("3.11.99"), semver.VersionInfo.parse("3.12.99")],
]


def remove_node_x_from_json(starter_dir):
    """remove node X from setup.json"""
    path_to_cfg = Path(starter_dir, "setup.json")
    content = {}
    with open(path_to_cfg, "r", encoding="utf-8") as setup_file:
        content = json.load(setup_file)
        peers = []
        reg_exp = re.compile(r"^.*\/nodeX$")
        for peer in content["peers"]["Peers"]:
            if not reg_exp.match(peer["DataDir"]):
                # Add only existing nodes. Skip nodeX peer
                peers.append(peer)
        content["peers"]["Peers"] = peers  # update 'peers' array

    with open(path_to_cfg, "w", encoding="utf-8") as setup_file:
        json.dump(content, setup_file)


class ClusterRBAC(Runner):
    """this launches a cluster setup"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes, disable=too-many-locals
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        selenium_include_suites,
        rp: RunProperties,
    ):
        name = "CLUSTER_RBAC" if not rp.force_one_shard else "FORCED_ONESHARD_CLUSTER_RBAC"
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties(rp, name, 400, 600, True, 6),
            selenium,
            selenium_driver_args,
            selenium_include_suites,
        )
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.create_test_collection = ""
        self.min_replication_factor = 2
        if self.props.cluster_nodes > 3:
            ver_found = 0
            versions = self.get_versions_concerned()
            for ver_pair in more_nodes_supported_starter:
                for version in versions:
                    if ver_pair[0] <= version < ver_pair[1]:
                        ver_found += 1
            if ver_found < len(versions):
                print("One deployment doesn't support starters with more nodes!")
                self.props.cluster_nodes = 3
        self.backup_instance_count = self.props.cluster_nodes
        # instantiate RBACHelper and do RBAC related setup
        self.rbh = RBACHelper(self.cfg.base_test_dir)
        self.rbh.create_jwt_folder_and_secret()
        self.rbh.provision_operator()
        self.su_token = self.rbh.generate_su_token()
        self.username = "admin"
        self.passvoid = self.username
        os.environ["RBAC_ADMIN_USER"] = self.username

    def starter_prepare_env_impl(self, sm=None, more_opts=None):
        # pylint: disable=invalid-name
        if more_opts is None:
            more_opts = []

        def add_starter(name, port, opts, sm, hasAgency):
            agencyInstance = []
            if hasAgency:
                agencyInstance = [InstanceType.AGENT]
            if sm is None:
                sm = StarterManager
            self.starter_instances.append(
                sm(
                    self.cfg,
                    self.is_foxx_supported,
                    self.basedir,
                    name,
                    mode="cluster",
                    jwt_str="cluster_rbac",
                    port=port,
                    expect_instances=agencyInstance
                    + [
                        InstanceType.COORDINATOR,
                        InstanceType.DBSERVER,
                    ],
                    moreopts=opts + more_opts,
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
        if self.props.replication2:
            common_opts += [
                "--dbservers.database.default-replication-version=2",
                "--coordinators.database.default-replication-version=2",
                "--args.all.log.level=replication2=debug",
                "--args.all.log.level=rep-state=debug",
            ]
        if self.props.force_one_shard:
            common_opts += ["--coordinators.cluster.force-one-shard=true", "--dbservers.cluster.force-one-shard=true"]
        else:
            common_opts += ["--args.all.cluster.default-replication-factor=2"]
        node_opts = []
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
        port = 8528
        count = 0
        # rbac options
        rbac_options = [
            "--args.all.server.rest-server=true",
            "--args.all.server.harden=true",
            f"--args.all.server.external-rbac-service={RBAC_SERVICE_GATEWAY}",
        ]
        common_opts.extend(rbac_options)
        # we need 2 additional nodes for hotbackup testing
        full_node_count = self.props.cluster_nodes
        # TODO BTS-2427: + 2 if self.hot_backup else self.props.cluster_nodes
        for this_node in list(range(1, full_node_count + 1)):
            node = []
            node_opts.append(node)
            if this_node != 1:
                node += ["--starter.join", "127.0.0.1:8528"]
            if self.cfg.ssl and not self.cfg.use_auto_certs:
                node_tls_keyfile = self.cert_dir / Path(f"node{this_node}") / "tls.keyfile"
                self.generate_keyfile(node_tls_keyfile)
                node.append(f"--ssl.keyfile={node_tls_keyfile}")
            add_starter(f"node{this_node}", port, node + common_opts, sm, count < 3)
            port += 10
            count += 1
        for instance in self.starter_instances:
            instance.is_leader = True
            instance.passvoid = self.passvoid

    def starter_run_impl(self):
        lh.subsection("instance setup")
        for manager in self.starter_instances[: self.props.cluster_nodes]:
            logging.info("Spawning instance")
            manager.run_starter()

        logging.info("waiting for the starters to become alive")
        not_running = self.get_running_starters()  # This is a explicit copy
        count = 0
        while not_running:
            logging.debug("waiting for mananger with logfile:" + str(not_running[-1].log_file))
            if not_running[-1].is_instance_up():
                not_running.pop()
            progress(".")
            time.sleep(1)
            count += 1
            if count > 120:
                raise Exception("Cluster installation didn't come up in two minutes!")

        logging.info("waiting for the cluster instances to become alive")
        for node in self.get_running_starters():
            node.detect_instances()
            node.detect_instance_pids()
            # self.cfg.add_frontend('http', self.cfg.publicip, str(node.get_frontend_port()))

        logging.info("instances are ready - JWT: " + self.starter_instances[0].get_jwt_header())

    def finish_setup_impl(self):
        self.makedata_instances = self.get_running_starters()
        self.set_frontend_instances()
        self.rbh.start_operator_services(self.get_fe_url())
        RBACHelper.create_rbac_admin_user(self.username, self.passvoid, self.get_fe_url(), self.su_token)

    def _check_for_shards_in_sync(self):
        """wait for all shards to be in sync"""
        lh.subsubsection("wait for all shards to be in sync - Jamming")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ["true"],
            verbose=True,
            log_debug=True,
        )
        if not retval:
            raise Exception("Failed to ensure the cluster is in sync: %s" % (retval))
        print("all in sync.")

    def test_setup_impl(self):
        if self.selenium:
            self.selenium.test_setup()

    def after_makedata_check(self):
        lh.subsubsection("wait for all shards to be in sync - test setup")
        # self._check_for_shards_in_sync()

    def wait_for_restore_impl(self, backup_starter):
        if self.hot_backup:
            for starter in self.starter_instances:
                for dbserver in starter.get_dbservers():
                    dbserver.detect_restore_restart()
        self._check_for_shards_in_sync()

    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        for node in self.get_running_starters():
            node.replace_binary_for_upgrade(self.new_installer.cfg)

        for node in self.get_running_starters():
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        if self.selenium:
            self.selenium.test_wait_for_upgrade()  # * 5s
        try:
            self.starter_instances[1].wait_for_upgrade(300)
        except TimeoutError as ex:
            for node in self.starter_instances:
                for instance in node.all_instances:
                    if instance.instance_type == InstanceType.COORDINATOR:
                        instance.crash_instance()
            raise ex
        for node in self.starter_instances:
            node.detect_instance_pids()
        self._check_for_shards_in_sync()

    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        lh.subsubsection("wait for all shards to be in sync - Manual upgrade")
        self._check_for_shards_in_sync()
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
        more_args = []
        if self.cfg.version != arangoversions['3126']:
            more_args = ['--cluster.upgrade=online']
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.DBSERVER
            ], ['--database.auto-upgrade', 'true',
                '--log.foreground-tty', 'true'] + more_args)
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

    def downgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        pass

    def _jam_stop_one_db_server(self):
        self.wait_data_impl()
        agency_leader = self.agency.get_leader()
        terminate_instance = 2
        survive_instance = 1
        if self.starter_instances[terminate_instance].have_this_instance(agency_leader):
            print("Cluster instance 2 has the agency leader; killing 1 instead")
            terminate_instance = 1
            survive_instance = 2

        instances = self.starter_instances[terminate_instance].get_dbservers()
        if len(instances) == 0:
            terminate_instance = 3
            instances = self.starter_instances[terminate_instance].get_dbservers()
        logging.info("stopping instance %d" % terminate_instance)
        uuid = instances[0].get_uuid()
        self.starter_instances[terminate_instance].terminate_instance(keep_instances=True)
        logging.info("relaunching agent!")
        self.starter_instances[terminate_instance].manually_launch_instances([InstanceType.AGENT], [], False, False)

        if self.replication2:
            self.remove_server_from_agency(uuid)

        self.set_frontend_instances()

        prompt_user(self.cfg, "instance stopped")
        if self.selenium:
            self.selenium.jam_step_1()
        deadline = 1800 if self.cfg.is_instrumented else 900
        progressive_timeout = 1000 if self.cfg.is_instrumented else 25
        if self.cfg.checkdata:
            for starter_instance in [self.starter_instances[0], self.starter_instances[survive_instance]]:
                for db_name, oneshard, count_offset in self.makedata_databases():
                    ret = starter_instance.arangosh.wait_test_data(
                        "Cluster one node missing",
                        self.is_foxx_supported,
                        starter_instance.supports_vector_index,
                        ["--disabledDbserverUUID", uuid, "--countOffset", str(count_offset)],
                        oneshard,
                        db_name,
                        mixed=self.mixed,
                        log_debug=True,
                        deadline=deadline,
                        progressive_timeout=progressive_timeout,
                    )
                    if not ret[0]:
                        raise Exception("check data failed in database %s :\n" % db_name + ret[1])
            for starter_instance in [self.starter_instances[0], self.starter_instances[survive_instance]]:
                for db_name, oneshard, count_offset in self.makedata_databases():
                    ret = starter_instance.arangosh.check_test_data(
                        "Cluster one node missing",
                        self.is_foxx_supported,
                        starter_instance.supports_vector_index,
                        ["--countOffset", str(count_offset)],
                        oneshard,
                        db_name,
                        mixed=self.mixed,
                        log_debug=True,
                        deadline=deadline,
                        progressive_timeout=progressive_timeout,
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

    def _jam_launch_unauthenticated_starter(self):
        moreopts = ["--starter.join", "127.0.0.1:8528"]
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
            self.is_foxx_supported,
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

    @step
    def jam_attempt_impl(self):
        # pylint: disable=too-many-statements disable=too-many-branches
        self._check_for_shards_in_sync()
        self._jam_stop_one_db_server()

        logging.info("jamming: Starting instance without jwt")
        self._jam_launch_unauthenticated_starter()
        # After attempt of jamming, we have peer for nodeX in setup.json.
        # This peer will brake further updates because this peer is unavailable.
        # It is necessary to remove this peer from json for each starter instance
        for instance in self.get_running_starters():
            remove_node_x_from_json(instance.basedir)

    def shutdown_impl(self):
        print("stopping the operator services...")
        self.rbh.stop_operator_services()
        os.environ.pop("RBAC_ADMIN_USER", None)
        ret = False
        for node in self.get_running_starters():
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
        pass

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

    def run_api_tests_impl(self):
        self.api_tests_failed = not APITestSuite(self.starter_instances[0]).run_api_tests()

    @step
    def remove_starter_dbserver(self, starter):
        """remove dbserver managed by given starter from cluster"""
        print("removing starter " + repr(starter))
        terminated_dbserver_uuid = starter.get_dbserver().get_uuid()
        starter.stop_dbserver()
        self.remove_server_from_agency(terminated_dbserver_uuid)
        self.backup_instance_count -= 1
        self.makedata_instances = self.get_running_starters()
        self._check_for_shards_in_sync()

    @step
    def test_hotbackup_after_upgrade_impl(self):
        """test hotbackup after upgrade: cluster"""
        with step("step 1: check data"):
            self.check_data_impl()
        with step("step 2: download backup"):
            latest_backup = self.uploaded_backups[-1]
            self.download_backup(latest_backup)
            backups = self.list_backup()
            if latest_backup not in backups:
                raise Exception("downloaded backup has different name? " + str(backups))
        with step("step 3: restore backup"):
            if self.restore_backup([latest_backup], 0):
                self.tcp_ping_all_nodes()
        # we don't run checkdata after restore in this function, because it is ran afterwards by in runner.py
        with step("step 4: delete backups"):
            self.delete_all_backups()

    def get_fe_url(self):
        fe_instance = [instance for instance in self.starter_instances[0].all_instances if instance.is_frontend()][0]
        return self.starter_instances[0].get_http_protocol() + "://" + fe_instance.get_public_plain_url()
