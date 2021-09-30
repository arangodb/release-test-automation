#!/usr/bin/env python3
""" baseclass to manage a starter based installation """
# pylint: disable=C0302
from abc import abstractmethod, ABC
import copy
import datetime
import json
import logging
from pathlib import Path
import os
import platform
import re
import shutil
import sys
import time

import certifi
import psutil
from reporting.reporting_utils import step
import requests

import tools.loghelper as lh
import tools.errorhelper as eh
import tools.interact as ti
from allure_commons._allure import attach

from arangodb.bench import load_scenarios
from arangodb.instance import InstanceType, print_instances_table
from arangodb.sh import ArangoshExecutor
from tools.killall import kill_all_processes

from arangodb.async_client import CliExecutionException

FNRX = re.compile("[\n@ ]*")
WINVER = platform.win32_ver()

def detect_file_ulimit():
    """ check whether the ulimit for files is to low """
    if not WINVER[0]:
        # pylint: disable=C0415
        import resource
        nofd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if nofd < 65535:
            raise Exception("please use ulimit -n <count>"
                            " to adjust the number of allowed"
                            " filedescriptors to a value greater"
                            " or eqaul 65535. Currently you have"
                            " set the limit to: " + str(nofd))
        giga_byte = 2**30
        resource.setrlimit(resource.RLIMIT_CORE, (giga_byte,giga_byte))

class RunnerProperties():
    """ runner properties management class """
    #pylint: disable=R0903 disable=R0913 disable=R0912
    def __init__(self,
                 short_name: str,
                 disk_usage_community: int,
                 disk_usage_enterprise: int,
                 supports_hotbackup: bool,
                 ssl: bool,
                 use_auto_certs: bool):
        self.short_name = short_name
        self.disk_usage_community = disk_usage_community
        self.disk_usage_enterprise = disk_usage_enterprise
        self.supports_hotbackup = supports_hotbackup
        self.ssl = ssl
        self.use_auto_certs = use_auto_certs

class Runner(ABC):
    """abstract starter deployment runner"""
# pylint: disable=R0913 disable=R0902 disable=R0904 disable=C0415 disable=R0914 disable=R0915
    def __init__(
            self,
            runner_type,
            abort_on_error: bool,
            install_set: list,
            properties: RunnerProperties,
            selenium_worker: str,
            selenium_driver_args: list,
            testrun_name: str):
        load_scenarios()
        assert runner_type, "no runner no cry? no!"
        logging.debug(runner_type)
        self.abort_on_error = abort_on_error
        self.testrun_name = testrun_name
        self.min_replication_factor = None
        self.state = ""
        self.runner_type = runner_type
        self.name = str(self.runner_type).split('.')[1]
        cfg = install_set[0][1].cfg
        old_inst = install_set[0][1]
        new_cfg = None
        new_inst = None
        if len(install_set) > 1:
            new_cfg = install_set[1][1].cfg
            new_inst = install_set[1][1]

        self.do_install = cfg.mode == "all" or cfg.mode == "install"
        self.do_uninstall = cfg.mode == "all" or cfg.mode == "uninstall"
        self.do_system_test = cfg.mode in [
            "all",
            "system"] and cfg.have_system_service
        self.do_starter_test = cfg.mode in ["all", "tests"]
        self.do_upgrade = False
        self.supports_rolling_upgrade = WINVER[0] == ''
        # self.supports_rolling_upgrade = False # TODO

        self.basecfg = copy.deepcopy(cfg)
        self.new_cfg = new_cfg
        self.cfg = self.basecfg
        self.cfg.ssl = properties.ssl
        self.cfg.use_auto_certs = properties.use_auto_certs
        self.certificate_auth = {}
        self.cert_dir = ""
        self.passvoid = None
        self.basecfg.passvoid = ""
        self.versionstr = ''
        if self.new_cfg:
            self.new_cfg.passvoid = ""   # TODO
            self.versionstr = "OLD[" + self.cfg.version + "] "

        self.basedir = Path(properties.short_name)
        count = 1
        while True:
            try:
                diskfree = shutil.disk_usage(str(self.basecfg.base_test_dir))
                break
            except FileNotFoundError:
                count += 1
                if count > 20:
                    break
                self.basecfg.base_test_dir.mkdir()
                print(self.basecfg.base_test_dir)
                print(self.basecfg.base_test_dir.exists())
                time.sleep(1)
                print('.')

        if count > 20:
            raise TimeoutError("disk_usage on " +
                               str(self.basecfg.base_test_dir) +
                               " not working")
        is_cleanup = self.cfg.version == "3.3.3"
        diskused = (properties.disk_usage_community
                    if not cfg.enterprise else properties.disk_usage_enterprise)
        if not is_cleanup and diskused * 1024 * 1024 > diskfree.free:
            logging.error("Scenario demanded %d MB "
                          "but only %d MB are available in %s",
                          diskused, diskfree.free / (1024*1024),
                          str(self.basecfg.base_test_dir))
            raise Exception("not enough free disk space to execute test!")

        self.old_installer = old_inst
        self.new_installer = new_inst
        self.backup_name = None
        self.hot_backup = ( cfg.hot_backup and
                            properties.supports_hotbackup and
                            self.old_installer.supports_hot_backup() )
        # self.hot_backup = False # TODO
        self.backup_instance_count = 3
        # starter instances that make_data wil run on
        # maybe it would be better to work directly on
        # frontends
        self.makedata_instances = []
        self.has_makedata_data = False

        # errors that occured during run
        self.errors = []
        self.starter_instances = []
        self.remote = len(self.basecfg.frontends) > 0
        if not self.remote:
            self.cleanup(False)
        if selenium_worker == "none":
            self.selenium = None
        else:
            print("Launching Browser %s %s" %(selenium_worker, str(selenium_driver_args)))
            from arangodb.starter.deployments.selenium_deployments import init as init_selenium
            self.selenium = init_selenium(
                runner_type,
                selenium_worker,
                selenium_driver_args,
                self.testrun_name,
                self.cfg.ssl)
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

    def progress(self, is_sub, msg, separator='x'):
        """ report user message, record for error handling. """
        if self.selenium:
            self.state += self.selenium.get_progress()
        if is_sub:
            if separator == 'x':
                separator = '='
            lh.subsection(msg, separator)
            self.state += "   - " + msg
        else:
            if separator == 'x':
                separator = '#'
            lh.section(msg, separator)
            self.state += "*** " + msg

        with step("Progress: " + msg):
            pass


    def ask_continue_or_exit(self, msg, output, default=True, status=1):
        """ ask the user whether to abort the execution or continue anyways """
        self.progress(False, msg)
        if not self.basecfg.interactive:
            raise Exception("%s:\n%s"%(msg, output))
        if not eh.ask_continue(msg, self.basecfg.interactive, default):
            print()
            print("Abort requested (default action)")
            raise Exception("must not continue from here - bye " + str(status))
        if self.abort_on_error:
            sys.exit(status)

    def get_progress(self):
        """ get user message reports """
        return self.state

    def take_screenshot(self):
        """ if we are a selenium enabled run, take a screenshot with the browser. """
        if self.selenium:
            self.selenium.take_screenshot()

    def run(self):
        """ run the full lifecycle flow of this deployment """
        # pylint: disable=R0915 disable=R0912
        if self.do_starter_test and not self.remote:
            detect_file_ulimit()

        self.progress(False, "Runner of type {0}".format(str(self.name)), "<3")

        if self.do_install or self.do_system_test:
            self.progress(False, "INSTALLATION for {0}".format(str(self.name)),)
            self.install(self.old_installer)
        else:
            self.basecfg.set_directories(self.old_installer.cfg)

        if self.do_starter_test:
            self.progress(False, "PREPARING DEPLOYMENT of {0}".format(str(self.name)),)
            self.starter_prepare_env()
            self.starter_run()
            self.finish_setup()
            self.make_data()
            if self.selenium:
                self.selenium.connect_server(self.get_frontend_instances(), '_system', self.cfg)
                self.selenium.check_old(self.old_installer.cfg)
            ti.prompt_user(
                self.basecfg,
                "{0}{1} Deployment started. Please test the UI!".format(
                    (self.versionstr),
                    str(self.name)))
            if self.hot_backup:
                self.progress(False, "TESTING HOTBACKUP")
                self.backup_name = self.create_backup("thy_name_is_" + self.name)
                self.tcp_ping_all_nodes()
                self.create_non_backup_data()
                backups = self.list_backup()
                print(backups)
                self.upload_backup(backups[0])
                self.tcp_ping_all_nodes()
                self.delete_backup(backups[0])
                self.tcp_ping_all_nodes()
                backups = self.list_backup()
                if len(backups) != 0:
                    raise Exception("expected backup to be gone, "
                                    "but its still there: " + str(backups))
                self.download_backup(self.backup_name)
                self.tcp_ping_all_nodes()
                backups = self.list_backup()
                if backups[0] != self.backup_name:
                    raise Exception("downloaded backup has different name? " +
                                    str(backups))
                self.before_backup()
                self.restore_backup(backups[0])
                self.tcp_ping_all_nodes()
                self.after_backup()
                self.check_data_impl()
                if not self.check_non_backup_data():
                    raise Exception("data created after backup"
                                    " is still there??")

        if self.new_installer:
            if self.hot_backup:
                self.create_non_backup_data()
            self.versionstr = "NEW[" + self.new_cfg.version + "] "

            self.progress(False, "UPGRADE OF DEPLOYMENT {0}".format(str(self.name)),)
            if self.cfg.have_debug_package:
                print('removing *old* debug package in advance')
                self.old_installer.un_install_debug_package()

            self.new_installer.upgrade_package(self.old_installer)
            lh.subsection("outputting version")
            self.new_installer.output_arangod_version()
            self.new_installer.get_starter_version()
            # only install debug package for new package.
            self.progress(True, 'installing debug package:')
            self.cfg.have_debug_package = self.new_installer.install_debug_package()
            if self.cfg.have_debug_package:
                self.new_installer.gdb_test()
            self.new_installer.stop_service()
            self.cfg.set_directories(self.new_installer.cfg)
            self.new_cfg.set_directories(self.new_installer.cfg)

            self.upgrade_arangod_version() #make sure to pass new version
            self.old_installer.un_install_package_for_upgrade()

            self.make_data_after_upgrade()
            if self.hot_backup:
                self.progress(False, "TESTING HOTBACKUP AFTER UPGRADE")
                backups = self.list_backup()
                print(backups)
                self.upload_backup(backups[0])
                self.tcp_ping_all_nodes()
                self.delete_backup(backups[0])
                self.tcp_ping_all_nodes()
                backups = self.list_backup()
                if len(backups) != 0:
                    raise Exception("expected backup to be gone, "
                                    "but its still there: " + str(backups))
                self.download_backup(self.backup_name)
                self.tcp_ping_all_nodes()
                backups = self.list_backup()
                if backups[0] != self.backup_name:
                    raise Exception("downloaded backup has different name? " +
                                    str(backups))
                time.sleep(20)# TODO fix
                self.before_backup()
                self.restore_backup(backups[0])
                self.tcp_ping_all_nodes()
                self.after_backup()
                if not self.check_non_backup_data():
                    raise Exception("data created after "
                                    "backup is still there??")
            self.check_data_impl()
        else:
            logging.info("skipping upgrade step no new version given")

        if self.do_starter_test:
            self.progress(False, "{0} TESTS FOR {1}".format(self.testrun_name, str(self.name)),)
            self.test_setup()
            self.jam_attempt()
            self.starter_shutdown()
            for starter in self.starter_instances:
                starter.detect_fatal_errors()
        if self.do_uninstall:
            self.uninstall(self.old_installer
                           if not self.new_installer else self.new_installer)
        if self.selenium:
            self.selenium.disconnect()
        self.progress(False, "Runner of type {0} - Finished!".format(str(self.name)))

    def run_selenium(self):
        """ fake to run the full lifecycle flow of this deployment """

        self.progress(False, "Runner of type {0}".format(str(self.name)), "<3")
        self.old_installer.load_config()
        self.old_installer.caclulate_file_locations()
        self.basecfg.set_directories(self.old_installer.cfg)
        if self.do_starter_test:
            self.progress(False, "PREPARING DEPLOYMENT of {0}".format(str(self.name)),)
            self.starter_prepare_env()
            self.finish_setup() # create the instances...
            for starter in self.starter_instances:
                # attach the PID of the starter instance:
                starter.attach_running_starter()
                # find out about its processes:
                starter.detect_instances()
            print(self.starter_instances)
            self.selenium.connect_server(self.get_frontend_instances(), '_system', self.cfg)
            self.selenium.check_old(self.old_installer.cfg)
        if self.new_installer:
            self.versionstr = "NEW[" + self.new_cfg.version + "] "

            self.progress(False, "UPGRADE OF DEPLOYMENT {0}".format(str(self.name)),)
            self.cfg.set_directories(self.new_installer.cfg)
            self.new_cfg.set_directories(self.new_installer.cfg)

        if self.do_starter_test:
            self.progress(False, "TESTS FOR {0}".format(str(self.name)),)
            #self.test_setup()
            #self.jam_attempt()
            #self.starter_shutdown()
        if self.selenium:
            self.selenium.disconnect()
        self.progress(False, "Runner of type {0} - Finished!".format(str(self.name)))

    @step
    def install(self, inst):
        """ install the package to the system """
        self.progress(True, "{0} - install package".format(str(self.name)))

        kill_all_processes(False)
        if self.do_install:
            lh.subsubsection("installing package")
            inst.install_package()
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

            lh.subsubsection("starting service")

            inst.start_service()

            inst.check_installed_paths()
            inst.check_engine_file()

            if not self.new_installer:
                # only install debug package for new package.
                self.progress(True, 'installing debug package:')
                self.cfg.have_debug_package = inst.install_debug_package()
                if self.cfg.have_debug_package:
                    self.progress(True, 'testing debug symbols')
                    inst.gdb_test()

        # start / stop
        if inst.check_service_up():
            inst.stop_service()
        inst.start_service()

        sys_arangosh = ArangoshExecutor(inst.cfg, inst.instance)

        logging.debug("self test after installation")
        if inst.cfg.have_system_service:
            sys_arangosh.self_test()

        if self.do_system_test:
            sys_arangosh.js_version_check()
            # TODO: here we should invoke Makedata for the system installation.

            logging.debug("stop system service "
                          "to make ports available for starter")
            inst.stop_service()

    @step
    def uninstall(self, inst):
        """ uninstall the package from the system """
        self.progress(True, "{0} - uninstall package".format(str(self.name)))
        if self.cfg.have_debug_package:
            print('uninstalling debug package')
            inst.un_install_debug_package()
        print('uninstalling server package')
        inst.un_install_package()
        inst.check_uninstall_cleanup()
        inst.cleanup_system()

    @step
    def starter_prepare_env(self):
        """ base setup; declare instance variables etc """
        self.progress(True, "{0} - prepare starter launch".format(str(self.name)))
        self.starter_prepare_env_impl()

    @step
    def starter_run(self):
        """
        now launch the starter instance s- at this point the basic setup is done
        """
        self.progress(True, "{0} - run starter instances".format(str(self.name)))
        self.starter_run_impl()

    @step
    def finish_setup(self):
        """ not finish the setup"""
        self.progress(True, "{0} - finish setup".format(str(self.name)))
        self.finish_setup_impl()

    @step
    def make_data(self):
        """ check if setup is functional """
        self.progress(True, "{0} - make data".format(str(self.name)))
        self.make_data_impl()

    @step
    def make_data_after_upgrade(self):
        """ check if setup is functional """
        self.progress(True, "{0} - make data after upgrade".format(str(self.name)))
        self.make_data_after_upgrade_impl()

    @step
    def test_setup(self):
        """ setup steps after the basic instances were launched """
        self.progress(True, "{0} - basic test after startup".format(str(self.name)))
        self.test_setup_impl()

    @step
    def upgrade_arangod_version(self):
        """ upgrade this installation """
        mode = "rolling" if self.supports_rolling_upgrade else "manual"
        self.progress(True, "{0} - {1} upgrade setup to newer version".format(
            str(self.name),
            mode
        ))
        logging.info("{1} -> {0}".format(
            self.new_installer.cfg.version,
            self.old_installer.cfg.version
        ))

        print("deinstall")
        print("install")
        print("replace starter")
        if self.supports_rolling_upgrade:
            print("upgrading instances in roling mode")
            self.upgrade_arangod_version_impl()
        else:
            print("upgrading instances in manual mode")
            self.upgrade_arangod_version_manual_impl()
        print("check data in instaces")

    @step
    def jam_attempt(self):
        """ check resilience of setup by obstructing its instances """
        self.progress(True, "{0}{1} - try to jam setup".format(
            self.versionstr,
            str(self.name)))
        self.jam_attempt_impl()

    @step
    def starter_shutdown(self):
        """ stop everything """
        self.progress(True, "{0}{1} - shutdown".format(
            self.versionstr,
            str(self.name)))
        self.shutdown_impl()

    @abstractmethod
    def shutdown_impl(self):
        """ the implementation shutting down this deployment """

    @abstractmethod
    def starter_prepare_env_impl(self):
        """ the implementation that prepares this deployment
            as creating directories etc."""

    @abstractmethod
    def finish_setup_impl(self):
        """ finalize the setup phase """

    @abstractmethod
    def starter_run_impl(self):
        """ the implementation that runs this actual deployment """

    @abstractmethod
    def test_setup_impl(self):
        """ run the tests on this deployment """

    @abstractmethod
    def upgrade_arangod_version_impl(self):
        """ rolling upgrade this deployment """

    @abstractmethod
    def upgrade_arangod_version_manual_impl(self):
        """ start/stop upgrade this deployment """

    @abstractmethod
    def jam_attempt_impl(self):
        """ if known, try to break this deployment """


    @step
    def set_frontend_instances(self):
        """ actualises the list of available frontends """
        self.basecfg.frontends = [] # reset the array...
        for frontend in self.get_frontend_instances():
            self.basecfg.add_frontend(self.get_http_protocol(),
                                      self.basecfg.publicip,
                                      frontend.port)

    def get_frontend_instances(self):
        """ fetch all frontend instances """
        frontends = []
        for starter in self.starter_instances:
            if not starter.is_leader:
                continue
            for frontend in starter.get_frontends():
                frontends.append(frontend)
        return frontends

    @step
    def tcp_ping_all_nodes(self):
        """ check whether all nodes react via tcp connection """
        for starter in self.starter_instances:
            starter.tcp_ping_nodes()

    @step
    def print_frontend_instances(self):
        """ print all http frontends to the user """
        frontends = self.get_frontend_instances()
        result = str()
        for frontend in frontends:
            result += frontend.get_public_url('root@')
        print(result)
        attach(result)

    @step
    def print_all_instances_table(self):
        """ print all http frontends to the user """
        instances = []
        for starter in self.starter_instances:
            instances += starter.get_instance_essentials()
        print_instances_table(instances)

    @step
    def print_makedata_instances_table(self):
        """ print all http frontends to the user """
        instances = []
        for starter in self.makedata_instances:
            instances += starter.get_instance_essentials()
        print_instances_table(instances)

    @step
    def make_data_impl(self):
        """ upload testdata into the deployment, and check it """
        assert self.makedata_instances, "don't have makedata instance!"
        logging.debug("makedata instances")
        self.print_makedata_instances_table()
        args = []
        if self.min_replication_factor:
            args += ['--minReplicationFactor', str(self.min_replication_factor)]

        for starter in self.makedata_instances:
            assert starter.arangosh, "make: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh

            #must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                try:
                    arangosh.create_test_data(self.name, args=args)
                except CliExecutionException as e:
                    if self.cfg.verbose:
                        print(e.execution_result[1])
                    self.ask_continue_or_exit(
                        "make_data failed for {0.name}".format(self),
                        e.execution_result[1],
                        False)
                self.has_makedata_data = True
            self.check_data_impl_sh(arangosh, starter.supports_foxx_tests)
        if not self.has_makedata_data:
            raise Exception("didn't find makedata instances, no data created!")


    @step
    def check_data_impl_sh(self, arangosh, supports_foxx_tests):
        """ check for data on the installation """
        if self.has_makedata_data:
            try:
                arangosh.check_test_data(self.name, supports_foxx_tests)
            except CliExecutionException as e:
                if not self.cfg.verbose:
                    print(e.execution_result[1])
                self.ask_continue_or_exit(
                    "check_data has data failed for {0.name}".format(self),
                    e.execution_result[1],
                    False)

    @step
    def check_data_impl(self):
        """ check for data on the installation """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.arangosh, "check: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return self.check_data_impl_sh(arangosh, starter.supports_foxx_tests)
        raise Exception("no frontend found.")

    @step
    def create_non_backup_data(self):
        """ create data to be zapped by the restore operation """
        for starter in self.makedata_instances:
            assert starter.arangosh, "non backup: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return arangosh.hotbackup_create_nonbackup_data()
        raise Exception("no frontend found.")

    @step
    def check_non_backup_data(self):
        """ check whether after a restore dummy data has vanished """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.arangosh, "check non backup: this starter doesn't have an arangosh!"
            arangosh = starter.arangosh
            return arangosh.hotbackup_check_for_nonbackup_data()
        raise Exception("no frontend found.")

    #TODO test make data after upgrade@abstractmethod
    def make_data_after_upgrade_impl(self):
        """ check the data after the upgrade """

    @step
    def before_backup(self):
        """ preparing SUT for the execution of the backup steps """
        self.progress(True, "{0} - preparing SUT for HotBackup".format(str(self.name)))
        self.before_backup_impl()

    @abstractmethod
    def before_backup_impl(self):
        """ preparing SUT for the execution of the backup steps """

    @step
    def after_backup(self):
        """ HotBackup has happened, prepare the SUT to continue testing """
        self.progress(True, "{0} - preparing SUT for tests after HotBackup".format(str(self.name)))
        self.after_backup_impl()

    @abstractmethod
    def after_backup_impl(self):
        """ HotBackup has happened, prepare the SUT to continue testing """

    @step
    def create_backup(self, name):
        """ create a backup on the installation """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "create backup: this starter doesn't have an hb instance!"
            return starter.hb_instance.create(name)
        raise Exception("no frontend found.")

    @step
    def list_backup(self):
        """ fetch the list of all backups known to the installation """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "list backup: this starter doesn't have an hb instance!"
            return starter.hb_instance.list()
        raise Exception("no frontend found.")

    @step
    def delete_backup(self, name):
        """ delete a hotbackup from an installation """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "delete backup: this starter doesn't have an hb instance!"
            return starter.hb_instance.delete(name)
        raise Exception("no frontend found.")

    # pylint: disable=R0201
    def wait_for_restore_impl(self, backup_starter):
        """ wait for all restores to be finished """
        backup_starter.wait_for_restore()

    @step
    def restore_backup(self, name):
        """ restore the named hotbackup to the installation """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "restore backup: this starter doesn't have an hb instance!"
            starter.hb_instance.restore(name)
            self.wait_for_restore_impl(starter)
            return
        raise Exception("no frontend found.")

    @step
    def upload_backup(self, name):
        """ upload a backup from the installation to a remote site """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "upload backup: this starter doesn't have an hb instance!"
            hb_id = starter.hb_instance.upload(name, starter.hb_config, "12345")
            return starter.hb_instance.upload_status(name,
                                                     hb_id,
                                                     self.backup_instance_count)
        raise Exception("no frontend found.")

    @step
    def download_backup(self, name):
        """ download a backup to the installation from remote """
        for starter in self.makedata_instances:
            if not starter.is_leader:
                continue
            assert starter.hb_instance, "download backup: this starter doesn't have an hb instance!"
            hb_id = starter.hb_instance.download(name,
                                                 starter.hb_config,
                                                 "12345")
            return starter.hb_instance.upload_status(name,
                                                     hb_id,
                                                     self.backup_instance_count)
        raise Exception("no frontend found.")

    @step
    def search_for_warnings(self):
        """ search for any warnings in any logfiles and dump them to the screen """
        for starter in self.starter_instances:
            print('Ww'*40)
            starter.search_for_warnings()
            for instance in starter.all_instances:
                print('w'*80)
                instance.search_for_warnings()

    @step
    def zip_test_dir(self):
        """ stores the test directory for later analysis """
        build_number = os.environ.get('BUILD_NUMBER')
        if build_number:
            build_number = '_' + build_number
        else:
            build_number = ''
        ver = self.cfg.version
        if self.new_cfg:
            ver += '_' + self.new_cfg.version

        filename = '%s_%s%s%s' % (
            FNRX.sub('', self.testrun_name),
            self.__class__.__name__,
            ver,
            build_number
        )
        if self.basecfg.base_test_dir.exists():
            archive = shutil.make_archive(filename,
                                "bztar",
                                self.basecfg.base_test_dir,
                                self.basedir)
            attach.file(archive, "test dir archive", "application/x-bzip2", "tar.bz2")
        else:
            print("test basedir doesn't exist, won't create report tar")

    @step
    def cleanup(self, reset_tmp=True):
        """ remove all directories created by this test """
        testdir = self.basecfg.base_test_dir / self.basedir
        print('cleaning up ' + str(testdir))
        if testdir.exists():
            shutil.rmtree(testdir)
            if "REQUESTS_CA_BUNDLE" in os.environ:
                del os.environ["REQUESTS_CA_BUNDLE"]
        if reset_tmp and WINVER[0]:
            os.environ["TMP"] = self.original_tmp
            os.environ["TEMP"] = self.original_temp
        elif "TMPDIR" in os.environ:
            del os.environ["TMPDIR"]

    @step
    def agency_trigger_leader_relection(self, old_leader):
        """ halt one agent to trigger an agency leader re-election """
        self.progress(True, "AGENCY pausing leader to trigger a failover\n%s"%repr(old_leader))
        old_leader.suspend_instance()
        time.sleep(1)
        while True:
            new_leader = self.agency_get_leader()
            if old_leader != new_leader:
                self.progress(True, "AGENCY failover has happened")
                break
            time.sleep(1)
        old_leader.resume_instance()
        if WINVER[0]:
            leader_mgr = None
            for starter_mgr in self.starter_instances:
                if starter_mgr.have_this_instance(old_leader):
                    leader_mgr = starter_mgr

            old_leader.kill_instance()
            time.sleep(5) # wait for the starter to respawn it...
            old_leader.detect_pid(leader_mgr.instance.pid)

    @step
    def agency_get_leader(self):
        """ get the agent that has the latest "serving" line """
        # please note: dc2dc has two agencies, this function cannot
        # decide between the two of them, and hence may give you
        # the follower DC agent as leader.
        agency = []
        for starter_mgr in self.starter_instances:
            agency += starter_mgr.get_agents()
        leader = None
        leading_date = datetime.datetime(1970, 1, 1, 0, 0, 0)
        for agent in agency:
            agent_leading_date = agent.search_for_agent_serving()
            if agent_leading_date > leading_date:
                leading_date = agent_leading_date
                leader = agent
        return leader

    @step
    def agency_acquire_dump(self):
        """ turns on logging on the agency """
        print("Duming agency")
        commands = [
            {
                'URL'   : '/_api/agency/config',
                'method': requests.get,
                'basefn': 'agencyConfig',
                'body'  : None
            }, {
                'URL'   :'/_api/agency/state',
                'method': requests.get,
                'basefn': 'agencyState',
                'body'  : None
            }, {
                'URL'   : '/_api/agency/read',
                'method': requests.post,
                'basefn': 'agencyPlan',
                'body'  : '[["/"]]'
            }
        ]
        for starter_mgr in self.starter_instances:
            try:
                for cmd in commands:
                    reply = starter_mgr.send_request(
                        InstanceType.AGENT,
                        cmd['method'],
                        cmd['URL'],
                        cmd['body'],
                        timeout=10)
                    print(reply)
                    count = 0
                    for repl in reply:
                        (starter_mgr.basedir / f"{cmd['basefn']}_{count}.json"
                         ).write_text(repl.text)
                        count += 1
            except requests.exceptions.RequestException as ex:
                # We skip one starter and all its agency dump attempts now.
                print("Error during an agency dump: " + str(ex))

    @step
    def agency_set_debug_logging(self):
        """ turns on logging on the agency """
        for starter_mgr in self.starter_instances:
            starter_mgr.send_request(
                InstanceType.AGENT,
                requests.put,
                '/_admin/log/level',
                '{"agency":"debug", "requests":"trace", '
                '"cluster":"debug", "maintenance":"debug"}')

    @step
    def dbserver_set_debug_logging(self):
        """ turns on logging on the dbserver """
        for starter_mgr in self.starter_instances:
            starter_mgr.send_request(
                InstanceType.DBSERVER,
                requests.put,
                '/_admin/log/level',
                '{"agency":"debug", "requests":"trace", '
                '"cluster":"debug", "maintenance":"debug"}')

    @step
    def coordinator_set_debug_logging(self):
        """ turns on logging on the coordinator """
        for starter_mgr in self.starter_instances:
            starter_mgr.send_request(
                InstanceType.COORDINATOR,
                requests.put,
                '/_admin/log/level',
                '{"agency":"debug", "requests":"trace", '
                '"cluster":"debug", "maintenance":"debug"}')

    @step
    def get_collection_list(self):
        """ get a list of collections and their shards """
        reply = self.starter_instances[0].send_request(
            InstanceType.COORDINATOR,
            requests.get,
            '/_api/collection',
            None)
        if reply[0].status_code != 200:
            raise Exception("get Collections: Unsupported return code" +
                            str(reply[0].status_code) +
                            " - " + str(reply[0].body))
        body_json = json.loads(reply[0].content)
        if body_json['code'] != 200:
            raise Exception("get Collections: Unsupported return code" +
                            str(reply[0].status_code) +
                            " - " + str(reply[0].body))
        collections = body_json['result']
        for collection in collections:
            collection['details'] = self.get_collection_cluster_details(collection['name'])
        return collections

    def get_collection_cluster_details(self, collection_name):
        """ get the shard details for a single collection """
        reply = self.starter_instances[0].send_request(
            InstanceType.COORDINATOR,
            requests.put,
            "/_db/_system/_admin/cluster/collectionShardDistribution",
           '{"collection": "%s"}'%(collection_name))
        if reply[0].status_code != 200:
            raise Exception("get Collection detail " + collection_name +
                            ": Unsupported return code" +
                            str(reply[0].status_code) +
                            " - " + str(reply[0].body))
        body_json = json.loads(reply[0].content)
        if body_json['code'] != 200:
            raise Exception("get Collection detail " + collection_name +
                            ": Unsupported return code" +
                            str(reply[0].status_code) +
                            " - " + str(reply[0].body))
        return body_json['results'][collection_name]

    # pylint: disable=R1705
    def get_protocol(self):
        """ return protocol of this starter (ssl/tcp) """
        if self.cfg.ssl:
            return "ssl"
        else:
            return "tcp"

    # pylint: disable=R1705
    def get_http_protocol(self):
        """ return protocol of this starter (http/https) """
        if self.cfg.ssl:
            return "https"
        else:
            return "http"

    def cert_op(self, args):
        """create a certificate"""
        print(args)
        create_cert = psutil.Popen([self.cfg.bin_dir / 'arangodb',
                                    'create'] +
                                   args)
        print("creating cert with PID:" + str(create_cert.pid))
        create_cert.wait()

    def create_cert_dir(self):
        """create certificate directory"""
        self.cert_dir = self.cfg.base_test_dir / self.basedir / "certs"
        self.cert_dir.mkdir(parents=True, exist_ok=True)

    def create_tls_ca_cert(self):
        """create a CA certificate"""
        if not self.cert_dir:
            self.create_cert_dir()
        self.certificate_auth["cert"] = self.cert_dir / 'tls-ca.crt'
        self.certificate_auth["key"] = self.cert_dir / 'tls-ca.key'
        self.cert_op(['tls', 'ca',
                 '--cert=' + str(self.certificate_auth["cert"]),
                 '--key=' + str(self.certificate_auth["key"])])
        self.register_ca_cert()

    def register_ca_cert(self):
        """configure requests lib to accept our custom CA certificate"""
        old_file = certifi.where()
        with open(old_file, 'rb') as file:
            old_certs = file.read()

        with open(self.certificate_auth["cert"], 'rb') as file:
            new_cert = file.read()

        new_file = self.cert_dir / 'ca_cert_storage.crt'
        with open(new_file, 'ab') as file:
            file.write(old_certs)
            file.write(new_cert)

        os.environ['REQUESTS_CA_BUNDLE'] = str(new_file)
