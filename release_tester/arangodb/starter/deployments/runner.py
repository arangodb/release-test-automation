#!/usr/bin/env python3
""" baseclass to manage a starter based installation """

from typing import Optional
from pathlib import Path
import logging

from abc import abstractmethod, ABC
import shutil
import tools.loghelper as lh
import tools.errorhelper as eh
import tools.interact as ti

from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig
from arangodb.sh import ArangoshExecutor
from tools.killall import kill_all_processes


class Runner(ABC):
    """abstract starter deployment runner"""

    def __init__(
            self,
            runner_type,
            cfg: InstallerConfig,
            old_inst: InstallerBase,
            new_cfg: InstallerConfig,
            new_inst: Optional[InstallerBase],
            short_name: str
        ):

        assert runner_type
        logging.debug(runner_type)
        self.runner_type = runner_type
        self.name = str(self.runner_type).split('.')[1]

        self.do_install = cfg.mode == "all" or cfg.mode == "install"
        self.do_uninstall = cfg.mode == "all" or cfg.mode == "uninstall"
        self.do_system_test = (cfg.mode == "all" or cfg.mode == "system") and cfg.have_system_service
        self.do_starter_test = cfg.mode == "all" or cfg.mode == "tests"
        self.do_upgrade = False

        self.basecfg = cfg
        self.new_cfg = new_cfg
        self.cfg = self.basecfg
        self.basecfg.passvoid = ""   # TODO: no passwd support in starter install yet.
        if self.new_cfg:
            self.new_cfg.passvoid = ""   # TODO

        self.basedir = Path(short_name)

        self.old_installer = old_inst
        self.new_installer = new_inst

        # starter instances that make_data wil run on
        # maybe it would be better to work directly on
        # frontends
        self.makedata_instances = []
        self.has_makedata_data = False

        # errors that occured during run
        self.errors = []

        #replacement for run function
        self.runner_run_replacement = None

        self.cleanup()

    def run(self):
        """ run the full lifecycle flow of this deployment """
        lh.section("Runner of type {0}".format(str(self.name)), "<3")

        if self.runner_run_replacement:
            """ use this to change the control flow for this runner"""
            self.runner_run_replacement()
            return

        if self.do_install or self.do_system_test:
            lh.section("INSTALLATION for {0}".format(str(self.name)),)
            self.install(self.old_installer)

        if self.do_starter_test:
            lh.section("PREPARING DEPLOYMENT of {0}".format(str(self.name)),)
            self.starter_prepare_env()
            self.starter_run()
            self.finish_setup()
            self.make_data()
            self.print_frontend_instances()
            ti.prompt_user(self.basecfg, "Deployment started. Please test the UI!")

        if self.new_installer:
            lh.section("UPGRADE OF DEPLOYMENT {0}".format(str(self.name)),)
            self.new_installer.upgrade_package()
            self.upgrade_arangod_version() #make sure to pass new version
            self.make_data_after_upgrade()
        else:
            logging.info("skipping upgrade step no new version given")

        if self.do_starter_test:
            lh.section("TESTS FOR {0}".format(str(self.name)),)
            self.test_setup()
            self.jam_attempt()
            self.starter_shutdown()
        if self.do_uninstall:
            self.uninstall(self.old_installer if not self.new_installer else self.new_installer)

        lh.section("Runner of type {0} - Finished!".format(str(self.name)))

    def install(self, inst):
        """ install the package to the system """
        lh.subsection("{0} - install package".format(str(self.name)))

        kill_all_processes()
        if self.do_install:
            lh.subsubsection("installing package")
            inst.install_package()
            lh.subsubsection("checking files")
            inst.check_installed_files()
            lh.subsubsection("saving config")
            inst.save_config()

            lh.subsubsection("checking if service is up")
            if inst.check_service_up():
                lh.subsubsection("stopping service")
                inst.stop_service()
            inst.broadcast_bind()
            lh.subsubsection("starting service")

            inst.start_service()

            inst.check_installed_paths()
            inst.check_engine_file()

            print('installing debug package: \n')
            inst.install_debug_package()
            if self.cfg.have_debug_package == True:
                inst.gdb_test()

        # start / stop
        if inst.check_service_up():
            inst.stop_service()
        inst.start_service()
        
        sys_arangosh = ArangoshExecutor(inst.cfg)

        logging.debug("self test after installation")
        sys_arangosh.self_test()

        if self.do_system_test:
            sys_arangosh.js_version_check()
            
            # TODO: here we should invoke Makedata for the system installation.

            logging.debug("stop system service to make ports available for starter")
            inst.stop_service()

      
    def uninstall(self, inst):
        """ uninstall the package from the system """
        print('checking for debug package installation status')
        if self.cfg.have_debug_package == True:
            print('Debug package installation found: ' + str(self.cfg.have_debug_package))
            inst.un_install_debug_package()

        lh.subsection("{0} - uninstall package".format(str(self.name)))

        inst.un_install_package()
        inst.check_uninstall_cleanup()
        inst.cleanup_system()

    def starter_prepare_env(self):
        """ base setup; declare instance variables etc """
        lh.subsection("{0} - prepare starter launch".format(str(self.name)))
        self.starter_prepare_env_impl()

    def starter_run(self):
        """ now launch the starter instance s- at this point the basic setup is done"""
        lh.subsection("{0} - run starter instances".format(str(self.name)))
        self.starter_run_impl()

    def finish_setup(self):
        """ not finish the setup"""
        lh.subsection("{0} - finish setup".format(str(self.name)))
        self.finish_setup_impl()

    def make_data(self):
        """ check if setup is functional """
        lh.subsection("{0} - make data".format(str(self.name)))
        self.make_data_impl()

    def make_data_after_upgrade(self):
        """ check if setup is functional """
        lh.subsection("{0} - make data after upgrade".format(str(self.name)))
        self.make_data_after_upgrade_impl()

    def test_setup(self):
        """ setup steps after the basic instances were launched """
        lh.subsection("{0} - basic test after startup".format(str(self.name)))
        self.test_setup_impl()

    def upgrade_arangod_version(self):
        """ upgrade this installation """
        lh.subsection("{0} - upgrade setup to newer version".format(str(self.name)))
        logging.info("{1} -> {0}".format(
            self.new_installer.cfg.version,
            self.old_installer.cfg.version
        ))

        print("deinstall")
        print("install")
        print("replace starter")
        print("upgrade instances")
        self.upgrade_arangod_version_impl()
        print("check data in instaces")


    def jam_attempt(self):
        """ check resilience of setup by obstructing its instances """
        lh.subsection("{0} - try to jam setup".format(str(self.name)))
        self.jam_attempt_impl()

    def starter_shutdown(self):
        """ stop everything """
        lh.subsection("{0} - shutdown".format(str(self.name)))

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
        """ upgrade this deployment """

    @abstractmethod
    def jam_attempt_impl(self):
        """ if known, try to break this deployment """

    def get_frontend_instances(self):
        frontends = []
        for starter in self.starter_instances:
            if not starter.is_leader:
                continue
            for frontend in starter.get_frontends():
                frontends.append(frontend)
        return frontends

    def print_frontend_instances(self):
        frontends = self.get_frontend_instances()
        for frontend in frontends:
            print(frontend.get_public_url('root@'))

    #@abstractmethod
    def make_data_impl(self):
        """ upload testdata into the deployment, and check it """
        assert self.makedata_instances
        logging.debug("makedata instances")
        for i in self.makedata_instances:
            logging.debug(str(i))

        interactive = self.basecfg.interactive

        for starter in self.makedata_instances:
            assert starter.arangosh
            arangosh = starter.arangosh

            #must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                success = arangosh.create_test_data(self.name)
                if not success:
                    eh.ask_continue_or_exit(
                        "make data failed for {0.name}".format(self),
                        interactive,
                        False)
                self.has_makedata_data = True

            if self.has_makedata_data:
                success = arangosh.check_test_data(self.name)
                if not success:
                    eh.ask_continue_or_exit(
                        "has data failed for {0.name}".format(self),
                        interactive,
                        False)

    #TODO test make data after upgrade@abstractmethod
    def make_data_after_upgrade_impl(self):
        """ check the data after the upgrade """
        pass

    def cleanup(self):
        """ remove all directories created by this test """
        testdir = self.basecfg.baseTestDir / self.basedir
        if testdir.exists():
            shutil.rmtree(testdir)
