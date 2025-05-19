#!/usr/bin/env python3
""" baseclass to manage a starter based installation """
# pylint: disable=too-many-lines
from abc import abstractmethod, ABC
import copy
from datetime import datetime, timedelta
import json
import logging
import os
from pathlib import Path
import platform
import re
import shutil
import sys
import time
import psutil
import py7zr

import reporting.reporting_utils
from allure_commons._allure import attach
import certifi
from beautifultable import BeautifulTable
import requests

import tools.errorhelper as eh
import tools.interact as ti
from tools.clihelper import run_cmd_and_log_stdout_async
from tools.killall import kill_all_processes
import tools.loghelper as lh
from tools.ulimits import detect_file_ulimit
from tools.locales import detect_locale
from tools.diskfree import check_diskfree
from reporting.reporting_utils import step

from arangodb.agency import Agency
from arangodb.async_client import CliExecutionException
from arangodb.bench import load_scenarios
from arangodb.instance import InstanceType, print_instances_table
from arangodb.installers.depvar import RunnerProperties
from arangodb.sh import ArangoshExecutor

FNRX = re.compile("[\n@ ]*")
WINVER = platform.win32_ver()
shutil.register_archive_format("7zip", py7zr.pack_7zarchive, description="7zip archive")


class Runner(ABC):
    """abstract starter deployment runner"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-public-methods disable=import-outside-toplevel disable=too-many-locals disable=too-many-statements disable=too-many-branches
    def __init__(
        self,
        runner_type,
        abort_on_error: bool,
        install_set: list,
        properties: RunnerProperties,
        selenium_worker: str,
        selenium_driver_args: list,
        selenium_include_suites: list,
    ):
        self.props = properties
        self.installers = install_set

        cfg = install_set[0][1].cfg
        old_inst = install_set[0][1]
        new_cfg = None
        new_inst = None
        self.must_create_backup = False
        if len(install_set) > 1:
            new_cfg = copy.deepcopy(install_set[1][1].cfg)
            new_inst = install_set[1][1]

        self.new_cfg = copy.deepcopy(new_cfg)
        self.cfg = copy.deepcopy(cfg)

        mem = psutil.virtual_memory()
        os.environ["ARANGODB_OVERRIDE_DETECTED_TOTAL_MEMORY"] = str(
            int((mem.total * 0.8) / properties.no_arangods_non_agency)
        )

        is_cleanup = self.cfg.version == "3.3.3"
        disk_used = properties.disk_usage_community if not cfg.enterprise else properties.disk_usage_enterprise
        if not is_cleanup:
            check_diskfree(self.cfg.base_test_dir, disk_used)

        load_scenarios()
        assert runner_type, "no runner no cry? no!"
        logging.debug(runner_type)
        self.abort_on_error = abort_on_error
        self.testrun_name = properties.testrun_name
        self.min_replication_factor = None
        self.agency = None
        self.state = ""
        self.runner_type = runner_type
        self.name = str(self.runner_type).split(".")[1]

        self.old_version = cfg.version  # The first version of ArangoDB which is used in current launch
        self.certificate_auth = {}
        self.cert_dir = ""
        self.checkdata_args = []
        self.passvoid = None
        self.versionstr = ""
        if self.new_cfg:
            self.new_cfg.passvoid = ""
            self.versionstr = "OLD[" + self.cfg.version + "] "

        self.basedir = Path(properties.short_name)
        self.ui_tests_failed = False
        self.ui_test_results_table = None
        self.old_installer = old_inst
        self.new_installer = new_inst
        self.backup_name = None
        self.uploaded_backups = []
        self.hot_backup = (
            cfg.hot_backup_supported and properties.supports_hotbackup and self.old_installer.supports_hot_backup()
        )
        self.backup_instance_count = 3
        # starter instances that make_data wil run on
        # maybe it would be better to work directly on
        # frontends
        self.makedata_instances = []
        self.has_makedata_data = False

        # list of databases to run makedata tests, besides "_system"
        self.custom_databases = []

        # errors that occured during run
        self.errors = []
        self.starter_instances = []
        self.remote = len(self.cfg.frontends) > 0
        if not self.remote:
            self.cleanup(False)
        if selenium_worker == "none":
            self.selenium = None
        else:
            print("Launching Browser %s %s" % (selenium_worker, str(selenium_driver_args)))
            from arangodb.starter.deployments.selenium_deployments import (
                init as init_selenium,
            )

            self.selenium = init_selenium(
                runner_type,
                self.props,
                selenium_worker,
                selenium_driver_args,
                selenium_include_suites,
                self.testrun_name,
                self.cfg.ssl,
            )
            print("Browser online")
        if WINVER[0]:
            self.original_tmp = os.environ["TMP"]
            self.original_temp = os.environ["TEMP"]
        if not is_cleanup:
            tmpdir = cfg.base_test_dir / properties.short_name / "tmp"
            tmpdir.mkdir(mode=0o777, parents=True, exist_ok=True)
            if WINVER[0]:
                os.environ["TMP"] = str(tmpdir)
                os.environ["TEMP"] = str(tmpdir)
            else:
                os.environ["TMPDIR"] = str(tmpdir)
            # only enable replication2 for clean installation tests
            # of versions 3.12.0 and above, and if it requested with CLI param
            self.replication2 = (
                properties.replication2
                and (
                    (self.old_installer.semver.major == 3 and self.old_installer.semver.minor >= 12)
                    or self.old_installer.semver.major > 3
                )
                and self.new_installer is None
            )
            self.upgrade_counter = 0

    def get_versions_concerned(self):
        """get all versions that will be worked on"""
        return [installer[1].semver for installer in self.installers]

    def progress(self, is_sub, msg, separator="x", supress_allure=False):
        """report user message, record for error handling."""
        if self.selenium:
            self.state += self.selenium.get_progress()
        if is_sub:
            if separator == "x":
                separator = "="
            lh.subsection(msg, separator)
            self.state += "   - " + msg
        else:
            if separator == "x":
                separator = "#"
            lh.section(msg, separator)
            self.state += "*** " + msg

        if not supress_allure:
            with step("Progress: " + msg):
                pass

    def ask_continue_or_exit(self, msg, output, default=True, status=1, invoking_exc=None):
        """ask the user whether to abort the execution or continue anyways"""
        self.progress(False, msg)
        if not self.cfg.interactive:
            if invoking_exc:
                raise Exception("%s:\n%s" % (msg, output)) from invoking_exc
            raise Exception("%s:\n%s" % (msg, output))
        if not eh.ask_continue(msg, self.cfg.interactive, default):
            print("Abort requested (default action)")
            raise Exception("must not continue from here - bye " + str(status))
        if self.abort_on_error:
            sys.exit(status)

    def get_progress(self):
        """get user message reports"""
        return self.state

    def take_screenshot(self):
        """if we are a selenium enabled run, take a screenshot with the browser."""
        if self.selenium:
            self.selenium.take_screenshot()

    def run(self):
        """run the full lifecycle flow of this deployment"""
        # pylint: disable=too-many-statements disable=too-many-branches
        if not self.remote:
            detect_file_ulimit()
            if self.cfg.check_locale:
                detect_locale()

        versions_count = len(self.installers)
        is_single_test = versions_count == 1
        bound = 1 if is_single_test else versions_count - 1

        for i in range(0, bound):
            self.old_installer = self.installers[i][1]
            if i == 0:
                # if i != 0, it means that self.cfg was already updated after chain-upgrade
                self.cfg = copy.deepcopy(self.old_installer.cfg)
            if not is_single_test:
                self.new_installer = self.installers[i + 1][1]
                self.new_cfg = copy.deepcopy(self.new_installer.cfg)

            is_keep_db_dir = i != bound - 1
            is_uninstall_now = i == bound - 1

            self.progress(False, "Runner of type {0}".format(str(self.name)), "<3")

            if i == 0:
                self.progress(
                    False,
                    "INSTALLATION for {0}".format(str(self.name)),
                )
                self.install(self.old_installer)
            else:
                self.cfg.set_directories(self.old_installer.cfg)

            self.progress(
                False,
                "PREPARING DEPLOYMENT of {0}".format(str(self.name)),
            )
            if i == 0:
                self.starter_prepare_env()
                self.starter_run()
                self.finish_setup()
            self.progress(True, "self test after installation")
            self.makedata_instances[0].arangosh.self_test()
            if self.props.create_oneshard_db:
                self.custom_databases.append(["system_oneshard_makedata", True, 1])
            self.make_data()
            self.after_makedata_check()
            self.check_data_impl()
            if self.selenium:
                self.set_selenium_instances()
                self.selenium.test_empty_ui()
            ti.prompt_user(
                self.cfg,
                "{0}{1} Deployment started. Please test the UI!".format((self.versionstr), str(self.name)),
            )
            if self.hot_backup:
                self.test_hotbackup()

            if self.new_installer:
                self.versionstr = "NEW[" + self.new_cfg.version + "] "

                self.upgrade_counter += 1
                self.progress(
                    False,
                    f"UPGRADE OF DEPLOYMENT {str(self.name)} #{str(self.upgrade_counter)}: "
                    f"from {str(self.old_installer.cfg.version)} to {str(self.new_installer.cfg.version)}.",
                )
                self.new_installer.calculate_package_names()
                try:
                    self.new_installer.upgrade_server_package(self.old_installer)
                finally:
                    self.new_installer.copy_binaries()
                lh.subsection("outputting version")
                self.new_installer.output_arangod_version()
                self.new_installer.get_starter_version()
                self.new_installer.get_sync_version()
                self.new_installer.get_rclone_version()
                self.new_installer.stop_service()

                self.upgrade_arangod_version()  # make sure to pass new version
                self.new_cfg.set_directories(self.new_installer.cfg)
                self.cfg = copy.deepcopy(self.new_cfg)

                self.old_installer.un_install_server_package_for_upgrade()
                if self.is_minor_upgrade() and self.new_installer.supports_backup():
                    self.new_installer.check_backup_is_created()
                if self.hot_backup:
                    self.test_hotbackup_after_upgrade()
                self.check_data_impl()
                self.versionstr = "OLD[" + self.new_cfg.version + "] "
            else:
                logging.info("skipping upgrade step no new version given")

            try:
                self.progress(
                    False,
                    "{0} TESTS FOR {1}".format(self.testrun_name, str(self.name)),
                )
                self.test_setup()
                self.jam_attempt()
                self.check_data_impl()
                if not is_keep_db_dir:
                    self.starter_shutdown()
                    for starter in self.get_running_starters():
                        starter.detect_fatal_errors()
                if is_uninstall_now:
                    self.uninstall(self.old_installer if not self.new_installer else self.new_installer)
            finally:
                if self.selenium:
                    ui_test_results_table = BeautifulTable(maxwidth=160)
                    for result in self.selenium.test_results:
                        ui_test_results_table.rows.append(
                            [result.name, "PASSED" if result.success else "FAILED", result.message, result.traceback]
                        )
                        if not result.success:
                            self.ui_tests_failed = True
                    ui_test_results_table.columns.header = ["Name", "Result", "Message", "Traceback"]
                    self.progress(False, "UI test results table:", supress_allure=True)
                    self.progress(False, "\n" + str(ui_test_results_table), supress_allure=True)
                    self.ui_test_results_table = ui_test_results_table

                    self.quit_selenium()

        self.progress(False, "Runner of type {0} - Finished!".format(str(self.name)))

    def test_hotbackup(self):
        self.progress(False, "TESTING HOTBACKUP")
        self.test_hotbackup_impl()

    def test_hotbackup_after_upgrade(self):
        self.progress(False, "TESTING HOTBACKUP AFTER UPGRADE")
        self.test_hotbackup_after_upgrade_impl()

    @step
    def test_hotbackup_impl(self):
        """test hotbackup feature: general implementation"""
        self.backup_name = self.create_backup("thy_name_is_" + self.name)
        self.validate_local_backup(self.backup_name)
        self.tcp_ping_all_nodes()
        self.create_non_backup_data()
        taken_backups = self.list_backup()
        backup_no = len(taken_backups) - 1
        self.upload_backup(taken_backups[backup_no])
        self.tcp_ping_all_nodes()
        self.delete_backup(taken_backups[backup_no])
        self.tcp_ping_all_nodes()
        backups = self.list_backup()
        if len(backups) != len(taken_backups) - 1:
            raise Exception("expected backup to be gone, " "but its still there: " + str(backups))
        self.download_backup(self.backup_name)
        self.validate_local_backup(self.backup_name)
        self.tcp_ping_all_nodes()
        backups = self.list_backup()
        if backups[len(backups) - 1] != self.backup_name:
            raise Exception("downloaded backup has different name? " + str(backups))
        self.before_backup()
        self.restore_backup(backups[len(backups) - 1])
        self.tcp_ping_all_nodes()
        self.after_backup()
        time.sleep(20)  # TODO fix
        self.check_data_impl()
        if not self.check_non_backup_data():
            raise Exception("data created after backup is still there??")

    @step
    def test_hotbackup_after_upgrade_impl(self):
        """test hotbackup after upgrade: general"""
        self.check_data_impl()
        backups = self.list_backup()
        self.upload_backup(backups[0])
        self.tcp_ping_all_nodes()
        self.delete_backup(backups[0])
        self.tcp_ping_all_nodes()
        backups = self.list_backup()
        if len(backups) != 0:
            raise Exception("expected backup to be gone, " "but its still there: " + str(backups))
        self.download_backup(self.backup_name)
        self.validate_local_backup(self.backup_name)
        self.tcp_ping_all_nodes()
        backups = self.list_backup()
        if backups[0] != self.backup_name:
            raise Exception("downloaded backup has different name? " + str(backups))
        time.sleep(20)  # TODO fix
        self.before_backup()
        self.restore_backup(backups[0])
        self.tcp_ping_all_nodes()
        self.after_backup()
        if not self.check_non_backup_data():
            raise Exception("data created after backup is still there??")
        self.delete_backup(backups[0])
        self.tcp_ping_all_nodes()
        backups = self.list_backup()
        if len(backups) != 0:
            raise Exception("expected backup to be gone, " "but its still there: " + str(backups))

    def run_selenium(self):
        """fake to run the full lifecycle flow of this deployment"""

        self.progress(False, "Runner of type {0}".format(str(self.name)), "<3")
        self.old_installer.load_config()
        self.old_installer.calculate_file_locations()
        self.cfg.set_directories(self.old_installer.cfg)
        self.progress(
            False,
            "PREPARING DEPLOYMENT of {0}".format(str(self.name)),
        )
        self.starter_prepare_env()
        self.finish_setup()  # create the instances...
        for starter in self.get_running_starters():
            # attach the PID of the starter instance:
            starter.attach_running_starter()
            # find out about its processes:
            starter.detect_instances()
        print(self.get_running_starters())
        self.selenium.test_after_install()
        if self.new_installer:
            self.versionstr = "NEW[" + self.new_cfg.version + "] "

            self.progress(
                False,
                "UPGRADE OF DEPLOYMENT {0}".format(str(self.name)),
            )
            self.new_cfg.set_directories(self.new_installer.cfg)

        self.progress(
            False,
            "TESTS FOR {0}".format(str(self.name)),
        )
        self.test_setup()
        self.jam_attempt()
        self.starter_shutdown()
        if self.selenium:
            self.selenium.disconnect()
        self.progress(False, "Runner of type {0} - Finished!".format(str(self.name)))

    @step
    def install(self, inst):
        """install the package to the system"""
        self.progress(True, "{0} - install package".format(str(self.name)))

        kill_all_processes(False)
        lh.subsubsection("installing server package")
        try:
            inst.install_server_package()
        finally:
            inst.copy_binaries()
        self.cfg.set_directories(inst.cfg)
        lh.subsubsection("checking files")
        inst.check_installed_files()
        lh.subsubsection("saving config")
        inst.save_config()
        lh.subsubsection("checking if service is up")
        if inst.check_service_up():
            lh.subsubsection("stopping service")
            inst.stop_service()
        inst.broadcast_bind()
        lh.subsubsection("outputting version")
        inst.output_arangod_version()
        inst.get_starter_version()
        inst.get_sync_version()
        inst.get_rclone_version()
        lh.subsubsection("starting service")
        inst.start_service()
        inst.check_installed_paths()
        inst.check_engine_file()

        if not self.new_installer:
            # only install debug package for new package.
            self.progress(True, "installing debug package:")

        # start / stop
        if inst.check_service_up():
            inst.stop_service()
        inst.start_service()
        sys_arangosh = ArangoshExecutor(inst.cfg, inst.instance, self.cfg.version)

        self.progress(True, "self test after installation")
        if inst.cfg.have_system_service:
            sys_arangosh.self_test()

            sys_arangosh.js_version_check()
        # TODO: here we should invoke Makedata for the system installation.
        self.progress(True, "stop system service to make ports available for starter")
        inst.stop_service()

    def get_selenium_status(self):
        """see whether we have a selenium success"""
        if not self.selenium:
            return True
        return self.selenium.success

    @step
    def quit_selenium(self):
        """if we have a selenium open, close it."""
        if self.selenium:
            self.selenium.quit()
            self.selenium = None

    @step
    def uninstall(self, inst):
        """uninstall the package from the system"""
        self.progress(True, "{0} - uninstall package".format(str(self.name)))
        print("uninstalling server package")
        inst.un_install_server_package()
        inst.check_uninstall_cleanup()
        inst.cleanup_system()

    @step
    def starter_prepare_env(self):
        """base setup; declare instance variables etc"""
        self.progress(True, "{0} - prepare starter launch".format(str(self.name)))
        self.starter_prepare_env_impl()
        self.agency = Agency(self)

    @step
    def starter_run(self):
        """
        now launch the starter instance s- at this point the basic setup is done
        """
        self.progress(True, "{0} - run starter instances".format(str(self.name)))
        self.starter_run_impl()
        self.export_instance_info()

    @step
    def finish_setup(self):
        """not finish the setup"""
        self.progress(True, "{0} - finish setup".format(str(self.name)))
        self.finish_setup_impl()

    @step
    def after_makedata_check(self):
        """just after makedata..."""

    @step
    def create_database(self, database_name: str, oneshard: bool = False):
        """create a new database"""
        arangosh = self.makedata_instances[0].arangosh
        cmd = 'db._createDatabase("%s", {%s})' % (database_name, '"sharding": "single"' if oneshard else "")
        arangosh.run_command(['create database "%s"' % database_name, cmd])

    @step
    def make_data(self):
        """check if setup is functional"""
        if not self.cfg.checkdata:
            self.progress(True, "{0} - skipping make data".format(str(self.name)))
            return
        self.progress(True, "{0} - make data".format(str(self.name)))
        self.make_data_impl()

    @step
    def test_setup(self):
        """setup steps after the basic instances were launched"""
        self.progress(True, "{0} - basic test after startup".format(str(self.name)))
        self.test_setup_impl()

    @step
    def upgrade_arangod_version(self):
        """upgrade this installation"""
        mode = "rolling" if self.cfg.supports_rolling_upgrade else "manual"
        self.progress(
            True,
            "{0} - {1} upgrade setup to newer version".format(str(self.name), mode),
        )
        logging.info("{0} -> {1}".format(self.old_installer.cfg.version, self.new_installer.cfg.version))

        print("deinstall\ninstall\nreplace starter")
        if self.cfg.supports_rolling_upgrade:
            print("upgrading instances in rolling mode")
            self.upgrade_arangod_version_impl()
        else:
            print("upgrading instances in manual mode")
            self.upgrade_arangod_version_manual_impl()
        print("check data in instances")

    @step
    def jam_attempt(self):
        """check resilience of setup by obstructing its instances"""
        self.progress(True, "{0}{1} - try to jam setup ".format(self.versionstr, str(self.name)))
        self.jam_attempt_impl()

    @step
    def starter_shutdown(self):
        """stop everything"""
        self.progress(True, "{0}{1} - shutdown".format(self.versionstr, str(self.name)))
        warnings_found = self.shutdown_impl()
        if warnings_found:
            raise Exception("warnings found during shutdown")

    @abstractmethod
    def shutdown_impl(self):
        """the implementation shutting down this deployment"""

    @abstractmethod
    def starter_prepare_env_impl(self):
        """the implementation that prepares this deployment
        as creating directories etc."""

    @abstractmethod
    def finish_setup_impl(self):
        """finalize the setup phase"""

    @abstractmethod
    def starter_run_impl(self):
        """the implementation that runs this actual deployment"""

    @abstractmethod
    def test_setup_impl(self):
        """run the tests on this deployment"""

    @abstractmethod
    def upgrade_arangod_version_impl(self):
        """rolling upgrade this deployment"""

    @abstractmethod
    def upgrade_arangod_version_manual_impl(self):
        """start/stop upgrade this deployment"""

    @abstractmethod
    def jam_attempt_impl(self):
        """if known, try to break this deployment"""

    @step
    def set_frontend_instances(self):
        """actualises the list of available frontends"""
        self.cfg.frontends = []  # reset the array...
        for frontend in self.get_frontend_instances():
            self.cfg.add_frontend(self.get_http_protocol(), self.cfg.publicip, frontend.port)

    def get_frontend_instances(self):
        """fetch all frontend instances"""
        frontends = []
        for starter in self.get_running_starters():
            if not starter.is_leader:
                continue
            for frontend in starter.get_frontends():
                frontends.append(frontend)
        return frontends

    def get_frontend_starters(self):
        """fetch all frontend instances"""
        frontends = []
        for starter in self.get_running_starters():
            if not starter.is_leader:
                continue
            if len(starter.get_frontends()) > 0:
                frontends.append(starter)
        return frontends

    @step
    def tcp_ping_all_nodes(self):
        """check whether all nodes react via tcp connection"""
        for starter in self.get_running_starters():
            starter.tcp_ping_nodes()

    @step
    def print_frontend_instances(self):
        """print all http frontends to the user"""
        frontends = self.get_frontend_instances()
        result = str()
        for frontend in frontends:
            result += frontend.get_public_url("root@")
        print(result)
        attach(result)

    @step
    def print_all_instances_table(self):
        """print all http frontends to the user"""
        instances = []
        for starter in self.get_running_starters():
            instances += starter.get_instance_essentials()
        print_instances_table(instances)

    @step
    def print_makedata_instances_table(self):
        """print all http frontends to the user"""
        instances = []
        for starter in self.makedata_instances:
            instances += starter.get_instance_essentials()
        print_instances_table(instances)

    @step
    def make_data_impl(self):
        """upload testdata into the deployment, and check it"""
        assert self.makedata_instances, "don't have makedata instance!"
        deadline = 3600 if self.cfg.is_instrumented else 900
        progressive_timeout = 1600 if self.cfg.is_instrumented else 100
        self.progress(True, "makedata instances")
        self.print_makedata_instances_table()
        args = [
            "--tempDataDir",
            str(self.cfg.base_test_dir / self.basedir / "makedata_tmp"),
            "--excludePreviouslyExecutedTests",
            "true",
        ]
        if self.min_replication_factor:
            args += ["--minReplicationFactor", str(self.min_replication_factor)]
        for starter in self.makedata_instances:
            assert starter.arangosh, "make: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh

            # must be writabe that the setup may not have already data
            if not arangosh.read_only:  # and not self.has_makedata_data:
                for db_name, one_shard, count_offset in self.makedata_databases():
                    try:
                        arangosh.create_test_data(
                            self.name,
                            args + ["--countOffset", str(count_offset)],
                            one_shard=one_shard,
                            database_name=db_name,
                            deadline=deadline,
                            progressive_timeout=progressive_timeout,
                        )
                    except CliExecutionException as exc:
                        if self.cfg.verbose:
                            print(exc.execution_result[1])
                        self.ask_continue_or_exit(
                            f"make_data failed for {self.name} in database {db_name} with {str(exc)}",
                            exc.execution_result[1],
                            False,
                            exc,
                        )
                self.has_makedata_data = True
        if not self.has_makedata_data:
            raise Exception("didn't find makedata instances, no data created!")

    @step
    def check_data_impl_sh(self, arangosh, supports_foxx_tests):
        """check for data on the installation"""
        deadline = 1800 if self.cfg.is_instrumented else 900
        progressive_timeout = 1000 if self.cfg.is_instrumented else 25
        if self.has_makedata_data:
            for db_name, one_shard, count_offset in self.makedata_databases():
                try:
                    arangosh.check_test_data(
                        self.name,
                        supports_foxx_tests,
                        args=["--countOffset", str(count_offset)] + self.checkdata_args,
                        database_name=db_name,
                        one_shard=one_shard,
                        deadline=deadline,
                        progressive_timeout=progressive_timeout,
                    )
                except CliExecutionException as exc:
                    if not self.cfg.verbose:
                        print(exc.execution_result[1])
                    self.ask_continue_or_exit(
                        f"check_data has failed for {self.name} in database {db_name} with {exc} - {exc.message}",
                        exc.execution_result[1],
                        False,
                        exc,
                    )

    @step
    def check_data_impl(self):
        """check for data on the installation"""
        if not self.cfg.checkdata:
            print("skipping makedata/checkdata")
            return

        frontend_found = False
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.arangosh, "check: this starter doesn't have an arangosh!"
            frontend_found = True
            arangosh = starter.arangosh
            self.check_data_impl_sh(arangosh, starter.supports_foxx_tests)
        if not frontend_found:
            raise Exception("no frontend found.")

    @step
    def create_non_backup_data(self):
        """create data to be zapped by the restore operation"""
        for starter in self.makedata_instances:
            assert starter.arangosh, "non backup: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return arangosh.hotbackup_create_nonbackup_data()
        raise Exception("no frontend found.")

    @step
    def check_non_backup_data(self):
        """check whether after a restore dummy data has vanished"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.arangosh, "check non backup: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return arangosh.hotbackup_check_for_nonbackup_data()
        raise Exception("no frontend found.")

    @step
    def before_backup(self):
        """preparing SUT for the execution of the backup steps"""
        self.progress(True, "{0} - preparing SUT for HotBackup".format(str(self.name)))
        self.before_backup_impl()

    @abstractmethod
    def before_backup_impl(self):
        """preparing SUT for the execution of the backup steps"""

    @abstractmethod
    def before_backup_create_impl(self):
        """preparing SUT for the execution of the backup steps"""

    @step
    def after_backup(self):
        """HotBackup has happened, prepare the SUT to continue testing"""
        self.progress(True, "{0} - preparing SUT for tests after HotBackup".format(str(self.name)))
        self.after_backup_impl()
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.arangosh, "check after backup: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return arangosh.hotbackup_wait_for_ready_after_restore()
        raise Exception("no frontend found.")

    @abstractmethod
    def after_backup_impl(self):
        """HotBackup has happened, prepare the SUT to continue testing"""

    @abstractmethod
    def after_backup_create_impl(self):
        """HotBackup has happened, prepare the SUT to continue testing"""

    @step
    def create_backup(self, name):
        """create a backup on the installation"""
        self.before_backup_create_impl()
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "create backup: this starter doesn't have an hb instance!"
            ret = starter.hb_instance.create(name)
            self.after_backup_create_impl()
            return ret
        raise Exception("no frontend found.")

    @step
    def list_backup(self):
        """fetch the list of all backups known to the installation"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "list backup: this starter doesn't have an hb instance!"
            return starter.hb_instance.list()
        raise Exception("no frontend found.")

    @step
    def delete_backup(self, name):
        """delete a hotbackup from an installation"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "delete backup: this starter doesn't have an hb instance!"
            return starter.hb_instance.delete(name)
        raise Exception("no frontend found.")

    @step
    def delete_all_backups(self):
        """delete all locally-stored backups"""
        for backup in self.list_backup():
            self.delete_backup(backup)

    def wait_for_restore_impl(self, backup_starter):
        """wait for all restores to be finished"""
        backup_starter.wait_for_restore()

    @step
    def restore_backup(self, name):
        """restore the named hotbackup to the installation"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "restore backup: this starter doesn't have an hb instance!"
            starter.hb_instance.restore(name)
            self.wait_for_restore_impl(starter)
            return
        raise Exception("no frontend found.")

    @step
    def upload_backup(self, name, timeout=1200):
        """upload a backup from the installation to a remote site"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "upload backup: this starter doesn't have an hb instance!"
            hb_id = starter.hb_instance.upload(name, starter.hb_config, "12345")
            starter.hb_instance.upload_status(name, hb_id, self.backup_instance_count, timeout=timeout)
            self.uploaded_backups.append(name)
            return
        raise Exception("no frontend found.")

    @step
    def download_backup(self, name, timeout=1200):
        """download a backup to the installation from remote"""
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "download backup: this starter doesn't have an hb instance!"
            hb_id = starter.hb_instance.download(name, starter.hb_config, "12345")
            return starter.hb_instance.upload_status(name, hb_id, self.backup_instance_count, timeout)
        raise Exception("no frontend found.")

    @step
    def validate_local_backup(self, name):
        """validate the local backup"""
        for starter in self.get_running_starters():
            assert starter.hb_instance, "download backup: this starter doesn't have an hb instance!"
            starter.hb_instance.validate_local_backup(starter.basedir, name)

    @step
    def create_backup_and_upload(self, backup_name, delete_local=True):
        """create a hotbackup, then upload and delete it"""
        backup_name = self.create_backup(backup_name)
        self.backup_name = backup_name
        self.validate_local_backup(self.backup_name)
        self.tcp_ping_all_nodes()
        taken_backups = self.list_backup()
        backup_no = len(taken_backups) - 1
        self.upload_backup(taken_backups[backup_no])
        self.tcp_ping_all_nodes()
        if delete_local:
            self.delete_backup(taken_backups[backup_no])
            self.tcp_ping_all_nodes()
            backups = self.list_backup()
            if len(backups) != len(taken_backups) - 1:
                raise Exception("expected backup to be gone, " "but its still there: " + str(backups))
        return backup_name

    @step
    def search_for_warnings(self, print_lines=True):
        """search for any warnings in any logfiles and dump them to the screen"""
        ret = False
        for starter in self.get_running_starters():
            print("Ww" * 40)
            starter.search_for_warnings()
            for instance in starter.all_instances:
                print("w" * 80)
                if instance.search_for_warnings(print_lines):
                    ret = True
        return ret

    @step
    def zip_test_dir(self):
        """💾 store the test directory for later analysis"""
        if reporting.reporting_utils.TARBALL_COUNT >= reporting.reporting_utils.TARBALL_LIMIT:
            print("skipping creation of test dir archive: limit for the number of archives is reached")
            return
        build_number = os.environ.get("BUILD_NUMBER")
        if build_number:
            build_number = "_" + build_number
        else:
            build_number = ""
        ver = self.cfg.version
        if self.new_cfg:
            ver += "_" + self.new_cfg.version

        filename = "%s_%s%s%s" % (
            FNRX.sub("", self.testrun_name),
            self.__class__.__name__,
            ver,
            build_number,
        )
        # keep binaries in a separate directory
        arangod_dir = self.cfg.base_test_dir / "arangods"
        arangod_dir.mkdir(parents=True)
        for installer_set in self.installers:
            installer_set[1].get_arangod_binary(arangod_dir)
        arangod_archive = shutil.make_archive(f"{filename}_arangod", "7zip", self.cfg.base_test_dir, "arangods")
        attach.file(arangod_archive, "binary dir archive", "application/x-7z-compressed", "7z")
        shutil.rmtree(arangod_dir)

        if self.cfg.base_test_dir.exists():
            print("zipping test dir")
            if self.hot_backup:
                for starter in self.get_running_starters():
                    starter.cleanup_hotbackup_in_instance()
                # we just assume that we might have the "remote" directory in this subdir:
                backup_dir = self.basedir / "backup"
                if backup_dir.exists():
                    for one_backup_dir in backup_dir.iterdir():
                        for node_dir in one_backup_dir.iterdir():
                            shutil.rmtree(node_dir / "views")
                            shutil.rmtree(node_dir / "engine_rocksdb")
            if self.cfg.log_dir.exists():
                logfile = self.cfg.log_dir / "arangod.log"
                targetfile = self.cfg.base_test_dir / self.basedir / "arangod.log"
                if logfile.exists():
                    print(f"copying {str(logfile)}* => {str(targetfile)} so it can be in the report")
                    for path in self.cfg.log_dir.glob("arangod.log*"):
                        shutil.copyfile(path, self.cfg.base_test_dir / self.basedir / path.name)
            archive = shutil.make_archive(filename, "7zip", self.cfg.base_test_dir, self.basedir)
            attach.file(archive, "test dir archive", "application/x-7z-compressed", "7z")
        else:
            print("test basedir doesn't exist, won't create report tar")
        reporting.reporting_utils.TARBALL_COUNT += 1

    @step
    def cleanup(self, reset_tmp=True):
        """remove all directories created by this test"""
        testdir = self.cfg.base_test_dir / self.basedir
        print("cleaning up " + str(testdir))
        try:
            if testdir.exists():
                shutil.rmtree(testdir)
        # pylint: disable=broad-except
        except Exception as ex:
            print(f"Ignoring cleanup error: {ex}")
        finally:
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
            if reset_tmp and WINVER[0]:
                os.environ["TMP"] = self.original_tmp
                os.environ["TEMP"] = self.original_temp
            elif "TMPDIR" in os.environ:
                del os.environ["TMPDIR"]

    def _set_logging(self, instance_type):
        """turn on logging for all of instance_type"""
        for starter_mgr in self.get_running_starters():
            starter_mgr.send_request(
                instance_type,
                requests.put,
                "/_admin/log/level",
                '{"agency":"debug", "requests":"trace", "cluster":"debug", "maintenance":"debug"}',
            )

    @step
    def agency_set_debug_logging(self):
        """turns on logging on the agency"""
        self._set_logging(InstanceType.AGENT)

    @step
    def dbserver_set_debug_logging(self):
        """turns on logging on the dbserver"""
        self._set_logging(InstanceType.DBSERVER)

    @step
    def coordinator_set_debug_logging(self):
        """turns on logging on the coordinator"""
        self._set_logging(InstanceType.COORDINATOR)

    @step
    def get_collection_list(self):
        """get a list of collections and their shards"""
        reply = self.get_running_starters()[0].send_request(InstanceType.COORDINATOR, requests.get, "/_api/collection", None)
        if reply[0].status_code != 200:
            raise Exception(
                "get Collections: Unsupported return code" + str(reply[0].status_code) + " - " + str(reply[0].body)
            )
        body_json = json.loads(reply[0].content)
        if body_json["code"] != 200:
            raise Exception(
                "get Collections: Unsupported return code" + str(reply[0].status_code) + " - " + str(reply[0].body)
            )
        collections = body_json["result"]
        for collection in collections:
            collection["details"] = self.get_collection_cluster_details(collection["name"])
        return collections

    def get_collection_cluster_details(self, collection_name):
        """get the shard details for a single collection"""
        reply = self.get_running_starters()[0].send_request(
            InstanceType.COORDINATOR,
            requests.put,
            "/_db/_system/_admin/cluster/collectionShardDistribution",
            '{"collection": "%s"}' % (collection_name),
        )
        if reply[0].status_code != 200:
            raise Exception(
                "get Collection detail "
                + collection_name
                + ": Unsupported return code"
                + str(reply[0].status_code)
                + " - "
                + str(reply[0].body)
            )
        body_json = json.loads(reply[0].content)
        if body_json["code"] != 200:
            raise Exception(
                "get Collection detail "
                + collection_name
                + ": Unsupported return code"
                + str(reply[0].status_code)
                + " - "
                + str(reply[0].body)
            )
        return body_json["results"][collection_name]

    # pylint: disable=no-else-return
    def get_protocol(self):
        """return protocol of this starter (ssl/tcp)"""
        if self.cfg.ssl:
            return "ssl"
        else:
            return "tcp"

    # pylint: disable=no-else-return
    def get_http_protocol(self):
        """return protocol of this starter (http/https)"""
        if self.cfg.ssl:
            return "https"
        else:
            return "http"

    def cert_op(self, args):
        """create a certificate"""
        print(args)
        cmd = [self.cfg.real_bin_dir / "arangodb", "create"] + args
        run_cmd_and_log_stdout_async(self.cfg, cmd)

    def create_cert_dir(self):
        """create certificate directory"""
        self.cert_dir = self.cfg.base_test_dir / self.basedir / "certs"
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def create_tls_ca_cert(self):
        """create a CA certificate"""
        if not self.cert_dir:
            self.create_cert_dir()
        self.certificate_auth["cert"] = self.cert_dir / "tls-ca.crt"
        self.certificate_auth["key"] = self.cert_dir / "tls-ca.key"
        self.cert_op(
            [
                "tls",
                "ca",
                "--cert=" + str(self.certificate_auth["cert"]),
                "--key=" + str(self.certificate_auth["key"]),
            ]
        )
        self.register_ca_cert()

    def register_ca_cert(self):
        """configure requests lib to accept our custom CA certificate"""
        old_file = certifi.where()
        with open(old_file, "rb") as file:
            old_certs = file.read()

        with open(self.certificate_auth["cert"], "rb") as file:
            new_cert = file.read()

        new_file = self.cert_dir / "ca_cert_storage.crt"
        with open(new_file, "ab") as file:
            file.write(old_certs)
            file.write(new_cert)

        os.environ["REQUESTS_CA_BUNDLE"] = str(new_file)

    def is_minor_upgrade(self):
        """do we only alter the third version digits?"""
        return self.new_installer.semver.minor > self.old_installer.semver.minor

    def set_selenium_instances(self):
        """set instances in selenium runner"""

    def export_instance_info(self):
        """resemble the testing.js INSTANCEINFO env"""
        starter_structs = []
        for starter in self.get_running_starters():
            starter_structs.append(starter.get_structure())
        struct = starter_structs[0]
        for starter in starter_structs[1:]:
            struct["arangods"].extend(starter["arangods"])
        os.environ["INSTANCEINFO"] = json.dumps(struct)

    def remove_server_from_agency(self, server_uuid, deadline=150):
        """remove server from the agency"""
        if self.agency is None:
            raise Exception("This deployment doesn't have an agency!")
        logging.info("Removing from agency the server with UUID: " + str(server_uuid))
        body = '{"server": "%s"}' % server_uuid
        deadline = datetime.now() + timedelta(seconds=deadline)
        while datetime.now() < deadline:
            reply = self.get_running_starters()[0].send_request(
                InstanceType.COORDINATOR,
                requests.post,
                "/_admin/cluster/removeServer",
                body,
            )
            if reply[0].status_code in (200, 404):
                return
            else:
                time.sleep(5)
        raise Exception(
            f"Cannot remove server from the agency.\n"
            f"Status code: {str(reply[0].status_code)}\n"
            f"Body: {str(reply[0].content)}"
        )

    def makedata_databases(self):
        """return a list of databases that makedata tests must be ran in"""
        return [["_system", self.props.force_one_shard, 0]] + self.custom_databases.copy()

    def get_running_starters(self):
        return [starter for starter in self.starter_instances if starter.is_running]

    def get_not_running_starters(self):
        return [starter for starter in self.starter_instances if not starter.is_running]