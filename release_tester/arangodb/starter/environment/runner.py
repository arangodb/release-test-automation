#!/usr/bin/env python3
""" baseclass to manage a starter based installation """

import shutil
from abc import abstractmethod, ABC


class Runner(ABC):
    """abstract starter environment runner"""
    basecfg = None
    basedir = NotImplemented

    @abstractmethod
    def setup(self):
        """ base setup; declare instance variables etc """

    @abstractmethod
    def run(self):
        """ now launch the stuff"""

    @abstractmethod
    def upgrade(self, newInstallCfg):
        """ upgrade this installation """

    @abstractmethod
    def post_setup(self):
        """ setup steps after the basic instances were launched """

    @abstractmethod
    def jam_attempt(self):
        """ check resilience of setup by obstructing its instances """

    @abstractmethod
    def shutdown(self):
        """ stop everything """

    def cleanup(self):
        """ remove all directories created by this test """
        testdir = self.basecfg.baseTestDir / self.basedir
        if testdir.exists():
            shutil.rmtree(testdir)
