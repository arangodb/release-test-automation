#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import re
import semver
import logging
from pathlib import Path

from tools.interact import prompt_user
from tools.killall import get_all_processes
from arangodb.starter.manager import StarterManager
from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner, RunnerProperties
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

from reporting.reporting_utils import step


class Single(Runner):
    """this runs a single server setup"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
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
            RunnerProperties("Single", 400, 500, True, ssl, use_auto_certs),
            selenium,
            selenium_driver_args,
            testrun_name,
        )

        self.starter_instance = None
        self.backup_instance_count = 1
        self.success = False

    def starter_prepare_env_impl(self):
        opts = []

        version = self.versionstr
        match = re.match(r"\w+\[(.+)\]", self.versionstr)
        if match:
            # upgrade
            version = match[1]
        
        if semver.compare(version, "3.9.5") == 0 or semver.compare(version, "3.10.2") >= 0:
            opts.append('--args.all.arangosearch.columns-cache-limit=500000')

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
            self.basecfg,
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
        tries = 30
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
        self.starter_instance.replace_binary_for_upgrade(self.new_cfg)
        self.starter_instance.command_upgrade()
        self.starter_instance.wait_for_upgrade()
        self.starter_instance.wait_for_upgrade_done_in_log()

        self.starter_instance.detect_instances()
        self.starter_instance.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    @step
    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        self.progress(True, "step 1 - shut down instances")
        instances = [self.starter_instance]
        self.starter_instance.replace_binary_setup_for_upgrade(self.new_cfg)
        self.starter_instance.terminate_instance(True)
        self.progress(True, "step 2 - launch instances with the upgrade options set")

        opts = ["--database.auto-upgrade", "true", "--javascript.copy-installation", "true"]

        print("\n\n\nVERSION ", self.versionstr)
        input("a")
        version = re.match(r"\w+\[(.+)\]", self.versionstr)[1]
        if semver.compare(version, "3.9.5") == 0 or semver.compare(version, "3.10.2") >= 0:
            input("b")
            opts.append('--args.all.arangosearch.columns-cache-limit')
            opts.append('500000')

        print("launch")
        self.starter_instance.manually_launch_instances(
                [InstanceType.SINGLE],
                opts,
            )
        self.progress(True, "step 3 - launch instances again")
        self.starter_instance.respawn_instance()
        self.progress(True, "step 4 - detect system state")
        self.starter_instance.detect_instances()
        self.starter_instance.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    @step
    def jam_attempt_impl(self):
        """run the replication fuzzing test"""
        prompt_user(self.basecfg, "please test the installation.")
        if self.selenium:
            self.selenium.test_jam_attempt()

    @step
    def shutdown_impl(self):
        self.starter_instance.terminate_instance()
        pslist = get_all_processes(False)
        if len(pslist) > 0:
            raise Exception("Not all processes terminated! [%s]" % str(pslist))
        logging.info("test ended")

    def before_backup_impl(self):
        """nothing to see here"""

    def after_backup_impl(self):
        """nothing to see here"""

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.starter_instance.arango_importer,
            self.starter_instance.arango_restore,
            self.starter_instance.all_instances[0],
        )
