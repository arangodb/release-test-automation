#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import sys
from pathlib import Path

import requests
from requests.auth import HTTPBasicAuth

from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from arangodb.starter.deployments.runner import Runner, RunnerProperties

from tools.asciiprint import print_progress as progress
from tools.interact import prompt_user


class ActiveFailover(Runner):
    """This launches an active failover setup"""

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
            RunnerProperties("ActiveFailOver", 500, 600, True, ssl, use_auto_certs),
            selenium,
            selenium_driver_args,
            testrun_name,
        )
        self.starter_instances = []
        self.follower_nodes = None
        self.leader = None
        self.first_leader = None
        self.new_leader = None
        self.success = True
        self.backup_instance_count = 1

    def _detect_leader(self):
        """find out the leader node"""
        self.leader = None
        while self.leader is None:
            for node in self.starter_instances:
                if node.detect_leader():
                    self.leader = node
                    self.first_leader = node
        self.first_leader.wait_for_version_reply()
        self.follower_nodes = []
        for node in self.starter_instances:
            node.detect_instance_pids()
            if not node.is_leader:
                self.follower_nodes.append(node)
            node.set_passvoid("leader", node.is_leader)

    def starter_prepare_env_impl(self):
        # fmt: off
        node1_opts = ['--all.log.level=replication=debug']
        node2_opts = ['--all.log.level=replication=debug', '--starter.join', '127.0.0.1:9528']
        node3_opts = ['--all.log.level=replication=debug', '--starter.join', '127.0.0.1:9528']
        # fmt: on
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
            node3_opts.append(f"--ssl.keyfile={node3_tls_keyfile}")

        def add_starter(name, port, opts):
            self.starter_instances.append(
                StarterManager(
                    self.basecfg,
                    self.basedir,
                    name,
                    mode="activefailover",
                    port=port,
                    expect_instances=[
                        InstanceType.AGENT,
                        InstanceType.RESILIENT_SINGLE,
                    ],
                    jwtStr="afo",
                    moreopts=opts,
                )
            )

        add_starter("node1", 9528, node1_opts)
        add_starter("node2", 9628, node2_opts)
        add_starter("node3", 9728, node3_opts)

    def starter_run_impl(self):
        logging.info("Spawning starter instances")
        for node in self.starter_instances:
            logging.info("Spawning starter instance in: " + str(node.basedir))
            node.run_starter()

        logging.info("waiting for the starters to become alive")
        while (
            not self.starter_instances[0].is_instance_up()
            and not self.starter_instances[1].is_instance_up()
            and not self.starter_instances[1].is_instance_up()
        ):
            sys.stdout.write(".")
            time.sleep(1)

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.active_failover_detect_hosts()

    def finish_setup_impl(self):
        logging.info("instances are ready, detecting leader. JWT: " + self.starter_instances[0].get_jwt_header())
        self._detect_leader()
        if self.selenium:
            self.set_selenium_instances()

        # add data to leader
        self.makedata_instances.append(self.leader)

        logging.info(
            "leader can be reached at: %s",
            self.leader.get_frontend().get_public_url(""),
        )
        self.set_frontend_instances()
        logging.info("active failover setup finished successfully")

    def test_setup_impl(self):
        self.success = True
        replies = []
        url = self.leader.get_frontend().get_local_url("")
        reply = requests.get(url, auth=HTTPBasicAuth("root", self.leader.passvoid))
        logging.info(str(reply))
        replies.append(reply)
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False

        url = self.follower_nodes[0].get_frontend().get_local_url("")
        reply = requests.get(url, auth=HTTPBasicAuth("root", self.leader.passvoid))
        logging.info(str(reply))
        logging.info(reply.text)
        replies.append(reply)
        if reply.status_code != 503:
            self.success = False

        url = self.follower_nodes[1].get_frontend().get_local_url("")
        reply = requests.get(url, auth=HTTPBasicAuth("root", self.leader.passvoid))
        logging.info(str(reply))
        logging.info(reply.text)
        replies.append(reply)
        if reply.status_code != 503:
            self.success = False
        logging.info("success" if self.success else "fail")
        if not self.success:
            raise Exception("leader/follower instances didn't reply as expected 200/503/503 " + str(replies))
        logging.info(
            "leader can be reached at: %s",
            self.leader.get_frontend().get_public_url(""),
        )
        ret = self.leader.arangosh.check_test_data(
            "checking active failover follower node", True, ["--readOnly", "false"]
        )
        if not ret[0]:
            raise Exception("check data failed " + ret[1])
        if self.selenium:
            self.set_selenium_instances()
            self.selenium.test_setup()

    def wait_for_restore_impl(self, backup_starter):
        backup_starter.wait_for_restore()
        self.leader = None
        retry = True
        time.sleep(5)  # Make shaky leader less viable.
        while retry:
            for node in self.starter_instances:
                if node.detect_leader():
                    if self.leader is not None:
                        print("Shaky leader?")
                        time.sleep(20)
                        retry = True
                        self.leader = None
                    else:
                        retry = False
                        self.leader = node

        if self.leader is None:
            raise Exception("wasn't able to detect the leader after restoring the backup!")
        print("Leader after restore: ")
        print(self.leader)
        # release from maintainance mode according to
        # https://www.arangodb.com/docs/3.7/programs-arangobackup-limitations.html#active-failover-special-limitations
        self.leader.maintainance(False, InstanceType.RESILIENT_SINGLE)

    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
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
            self.selenium.test_wait_for_upgrade()

    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        self.progress(True, "manual upgrade step 1 - stop system")
        self.leader.maintainance(True, InstanceType.RESILIENT_SINGLE)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_cfg)
            node.terminate_instance(True)
        self.progress(True, "step 2 - upgrade database directories")
        for node in self.starter_instances:
            print("launch")
            node.manually_launch_instances([InstanceType.AGENT], ["--database.auto-upgrade", "true"])
        for node in self.starter_instances:
            print("launch")
            node.manually_launch_instances(
                [
                    InstanceType.RESILIENT_SINGLE,
                ],
                ["--database.auto-upgrade", "true", "--javascript.copy-installation", "true"],
            )
        self.progress(True, "step 3 - launch instances again")
        for node in self.starter_instances:
            node.respawn_instance()
        self.progress(True, "step 4 - check alive status")
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()
        self._detect_leader()
        self.leader.maintainance(False, InstanceType.RESILIENT_SINGLE)
        self.print_all_instances_table()
        if self.selenium:
            self.selenium.test_wait_for_upgrade()

    def jam_attempt_impl(self):
        # pylint: disable=R0915
        agency_leader = self.agency_get_leader()
        if self.first_leader.have_this_instance(agency_leader):
            print("AFO-Leader and agency leader are attached by the same starter!")
            self.agency_trigger_leader_relection(agency_leader)

        self.first_leader.terminate_instance(keep_instances=True)
        logging.info("relaunching agent!")
        self.first_leader.manually_launch_instances([InstanceType.AGENT], [], False, False)

        logging.info("waiting for new leader...")
        self.new_leader = None

        count = 0
        while self.new_leader is None:
            for node in self.follower_nodes:
                node.detect_instance_pids_still_alive()
                node.detect_leader()
                if node.is_leader:
                    logging.info("have a new leader: %s", str(node.arguments))
                    self.new_leader = node
                    self.leader = node
                    break
                progress(".")
            time.sleep(1)
            if count > 360:
                # self.progress(False, "Timeout waiting for new leader - crashing!")
                # for node in self.starter_instances:
                #    node.crash_instances()
                raise TimeoutError("Timeout waiting for new leader!")
            count += 1

        print()
        ret = self.new_leader.arangosh.check_test_data("checking active failover new leader node", True)
        if not ret[0]:
            raise Exception("check data failed " + ret[1])

        logging.info("\n" + str(self.new_leader))
        url = "{host}/_db/_system/_admin/aardvark/index.html#replication".format(
            host=self.new_leader.get_frontend().get_local_url("")
        )
        reply = requests.get(url, auth=HTTPBasicAuth("root", self.leader.passvoid))
        logging.info(str(reply))
        if reply.status_code != 200:
            logging.info(reply.text)
            self.success = False
        self.set_frontend_instances()

        if self.selenium:
            # cfg = self.new_cfg if self.new_cfg else self.cfg
            self.set_selenium_instances()
            self.selenium.test_jam_attempt()

        prompt_user(
            self.basecfg,
            """The leader failover has happened.
please revalidate the UI states on the new leader; you should see *one* follower.""",
        )
        self.first_leader.respawn_instance()
        self.first_leader.detect_instances()
        logging.info("waiting for old leader to show up as follower")
        while not self.first_leader.active_failover_detect_host_now_follower():
            progress(".")
            time.sleep(1)
        print()

        url = self.first_leader.get_frontend().get_local_url("")

        reply = requests.get(url, auth=HTTPBasicAuth("root", self.leader.passvoid))
        logging.info(str(reply))
        logging.info(str(reply.text))

        if reply.status_code != 503:
            self.success = False

        prompt_user(
            self.basecfg,
            "The old leader has been respawned as follower (%s),"
            " so there should be two followers again." % self.first_leader.get_frontend().get_public_url("root@"),
        )

        logging.info("state of this test is: %s", "Success" if self.success else "Failed")
        if self.selenium:
            # cfg = self.new_cfg if self.new_cfg else self.cfg
            self.set_selenium_instances()
            self.selenium.test_wait_for_upgrade()

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()

        logging.info("test ended")

    def before_backup_impl(self):
        """put into maintainance mode according to
        https://www.arangodb.com/docs/3.7/programs-arangobackup-limitations.html#active-failover-special-limitations
        """
        self.leader.maintainance(True, InstanceType.RESILIENT_SINGLE)

    def after_backup_impl(self):
        pass

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.leader.arango_importer,
            self.leader.arango_restore,
            [x for x in self.leader.all_instances if x.instance_type == InstanceType.RESILIENT_SINGLE][0],
            self.new_cfg,
        )
