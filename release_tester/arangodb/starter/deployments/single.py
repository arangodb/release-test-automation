#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import logging
from pathlib import Path
import time

import requests

from tools.interact import prompt_user
from tools.killall import get_all_processes
from arangodb.starter.manager import StarterManager
from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner, RunnerProperties
import tools.loghelper as lh

from reporting.reporting_utils import step


class Single(Runner):
    """this runs a single server setup"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=unused-argument
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        testrun_name: str,
        ssl: bool,
        replication2: bool,
        use_auto_certs: bool,
    ):
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("Single", 400, 500, True, ssl, False, use_auto_certs, 1),
            selenium,
            selenium_driver_args,
            testrun_name,
        )

        self.starter_instance = None
        self.backup_instance_count = 1
        self.success = False

    def starter_prepare_env_impl(self):
        opts = []
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
            tls_keyfile = self.cert_dir / Path("single") / "tls.keyfile"
            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            opts.append(f"--ssl.keyfile={tls_keyfile}")

        self.starter_instance = StarterManager(
            self.cfg,
            self.basedir,
            "single",
            mode="single",
            port=1234,
            expect_instances=[InstanceType.SINGLE],
            jwt_str="single",
            moreopts=opts,
        )
        self.starter_instance.is_leader = True

    def starter_run_impl(self):
        self.starter_instance.run_starter()

        self.starter_instance.detect_instances()

        self.starter_instance.detect_instance_pids()

        self.passvoid = "single"
        self.starter_instance.set_passvoid(self.passvoid)

        self.starter_instances = [
            self.starter_instance,
        ]

    def finish_setup_impl(self):
        # finish setup by starting the replications
        self.set_frontend_instances()

        self.makedata_instances.append(self.starter_instance)

    @step
    def test_setup_impl(self):
        logging.info("testing the single server setup")
        lh.subsection("single server - check test data", "-")

        if self.selenium:
            self.selenium.test_after_install()
        self.make_data()
        if self.selenium:
            self.selenium.test_setup()

        logging.info("Single setup successfully finished!")

    @step
    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        self.starter_instance.replace_binary_for_upgrade(self.new_installer.cfg)
        self.starter_instance.command_upgrade()
        self.starter_instance.wait_for_upgrade()
        self.starter_instance.wait_for_upgrade_done_in_log()

        self.starter_instance.detect_instances()
        self.starter_instance.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    def wait_for_restore_impl(self, backup_starter):
        print("wait start")
        super().wait_for_restore_impl(backup_starter)
        time.sleep(1)
        print("ping")
        self.starter_instance.tcp_ping_nodes(timeout=60.0)

    @step
    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        self.progress(True, "step 1 - shut down instances")
        self.starter_instance.replace_binary_setup_for_upgrade(self.new_installer.cfg)
        self.starter_instance.terminate_instance(True)
        self.progress(True, "step 2 - launch instances with the upgrade options set")
        print("launch")
        self.starter_instance.manually_launch_instances(
            [InstanceType.SINGLE],
            ["--database.auto-upgrade", "true", "--javascript.copy-installation", "true"],
        )
        self.progress(True, "step 3 - launch instances again")
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        self.starter_instance.respawn_instance(version)
        self.progress(True, "step 4 - detect system state")
        self.starter_instance.detect_instances()
        self.starter_instance.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    @step
    def jam_attempt_impl(self):
        """run the replication fuzzing test"""
        prompt_user(self.cfg, "please test the installation.")
        if self.selenium:
            self.selenium.test_jam_attempt()

    @step
    def shutdown_impl(self):
        ret = self.starter_instance.terminate_instance()
        pslist = get_all_processes(False)
        if len(pslist) > 0:
            raise Exception("Not all processes terminated! [%s]" % str(pslist))
        logging.info("test ended")
        return ret

    def before_backup_create_impl(self):
        pass

    def after_backup_create_impl(self):
        pass

    def before_backup_impl(self):
        """nothing to see here"""

    def after_backup_impl(self):
        """nothing to see here"""
        time.sleep(1)
        count = 0
        while True:
            try:
                reply = self.starter_instance.send_request(InstanceType.SINGLE, requests.get, "/_api/collection", None)
                if reply[0].status_code == 200:
                    break
            # pylint: disable=broad-except
            except Exception:
                print("waiting")
            count += 1
            if count > 50:
                raise Exception("system doesn't become responsive after restore")
            time.sleep(1)

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.starter_instance.arango_importer,
            self.starter_instance.arango_restore,
            self.starter_instance.all_instances[0],
        )
