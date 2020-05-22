#!/usr/bin/env python3
""" baseclass to manage a starter based installation """

import shutil
from pathlib import Path
from abc import abstractmethod, ABC
import logging
import tools.loghelper as lh
import tools.errorhelper as eh

from typing import Optional
from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig
from pprint import pprint as PP


class Runner(ABC):
    """abstract starter deployment runner"""

    def __init__(
            self,
            runner_type,
            cfg: InstallerConfig,
            old_inst: InstallerBase,
            new_inst: Optional[InstallerBase],
            short_name: str
        ):

        assert(runner_type)
        logging.debug(runner_type)
        self.runner_type = runner_type
        self.name = str(self.runner_type).split('.')[1]

        self.basecfg = cfg
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
        lh.section("Runner of type {0}".format(str(self.name)))

        if self.runner_run_replacement:
            """ use this to change the control flow for this runner"""
            self.runner_run_replacement()
            return

        self.starter_prepare_env()
        self.starter_run()
        self.finish_setup()
        self.make_data()

        if self.new_installer:
            self.upgrade_arangod_version() #make sure to pass new version
            self.make_data_after_upgrade()
        else:
            logging.info("skipping upgrade step no new version given")

        self.test_setup()
        self.jam_attempt()
        self.starter_shutdown()

        lh.section("Runner of type {0} - Finished!".format(str(self.name)))

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
        lh.subsection("{0} - shutdown".format(str(self.name)))
        """ stop everything """

    @abstractmethod
    def shutdown_impl(self):
        pass

    @abstractmethod
    def starter_prepare_env_impl(self):
        pass

    @abstractmethod
    def starter_run_impl(self):
        pass

    @abstractmethod
    def finish_setup_impl(self):
        pass

    @abstractmethod
    def test_setup_impl(self):
        pass

    @abstractmethod
    def upgrade_arangod_version_impl(self):
        pass

    @abstractmethod
    def jam_attempt_impl(self):
        pass

    @abstractmethod
    def shutdown_impl(self):
        pass

    #@abstractmethod
    def make_data_impl(self):
        assert(self.makedata_instances)
        interactive =  self.basecfg.interactive

        for starter in self.makedata_instances:
            assert(starter.arangosh)
            arangosh = starter.arangosh

            #must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                success = arangosh.create_test_data(self.name)
                if not success:
                    eh.ask_continue_or_exit("make data failed for {0.name}".format(self), interactive, False)
                self.has_makedata_data = True

            if self.has_makedata_data:
                success = arangosh.check_test_data(self.name)
                if not success:
                    eh.ask_continue_or_exit("has data failed for {0.name}".format(self), interactive, False)

    #@abstractmethod
    def make_data_after_upgrade_impl(self):
        pass

    def cleanup(self):
        """ remove all directories created by this test """
        testdir = self.basecfg.baseTestDir / self.basedir
        if testdir.exists():
            shutil.rmtree(testdir)

