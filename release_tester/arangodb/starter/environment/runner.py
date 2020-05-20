#!/usr/bin/env python3
""" baseclass to manage a starter based installation """

import shutil
from pathlib import Path
from abc import abstractmethod, ABC
import logging
import tools.loghelper as lh

from typing import Optional
from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig
from pprint import pprint as PP

class Runner(ABC):
    """abstract starter environment runner"""

    def __init__(self, runner_type, cfg: InstallerConfig, old_inst: InstallerBase, new_inst: Optional[InstallerBase], short_name: str):

        assert(runner_type)
        logging.debug(runner_type)

        self.basecfg = cfg
        self.basedir = Path(short_name)

        self.old_installer = old_inst
        self.new_installer = new_inst

        self.runner_type = runner_type
        self.runner_run_replacement = None

        # errors that occured during run
        self.errors = []

        self.cleanup()

    def run(self):
        lh.section("Runner of type {0}".format(str(self.runner_type)))

        if self.runner_run_replacement:
            """ use this to change the control flow for this runner"""
            self.runner_run_replacement()
            return

        if self.runner_type:
            self.starter_prepare_env()
            self.starter_run()
            self.finish_setup()
            self.test_setup()
            self.upgrade_arangod_version() #make sure to pass new version
            self.jam_attempt()
            self.starter_shutdown()

        lh.section("Runner of type {0} - Finished!".format(str(self.runner_type)))

    def starter_prepare_env(self):
        """ base setup; declare instance variables etc """
        lh.subsection("{0} - prepare starter launch".format(str(self.runner_type)))
        self.starter_prepare_env_impl()

    def starter_run(self):
        """ now launch the starter instance s- at this point the basic setup is done"""
        lh.subsection("{0} - run starter instances".format(str(self.runner_type)))
        self.starter_run_impl()

    def finish_setup(self):
        """ not finish the setup"""
        lh.subsection("{0} - finish setup".format(str(self.runner_type)))
        self.finish_setup_impl()

    def test_setup(self):
        """ setup steps after the basic instances were launched """
        lh.subsection("{0} - basic test after startup".format(str(self.runner_type)))
        self.test_setup_impl()

    def upgrade_arangod_version(self):
        """ upgrade this installation """
        if not self.new_installer:
            logging.info("skipping upgrade step no new version given")
            return

        lh.subsection("{0} - upgrade setup to newer version".format(str(self.runner_type)))
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
        lh.subsection("{0} - try to jam setup".format(str(self.runner_type)))
        self.jam_attempt_impl()

    def starter_shutdown(self):
        lh.subsection("{0} - shutdown".format(str(self.runner_type)))
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

    def cleanup(self):
        """ remove all directories created by this test """
        testdir = self.basecfg.baseTestDir / self.basedir
        if testdir.exists():
            shutil.rmtree(testdir)

