#!/usr/bin/env python3
""" inbetween class for windows specific utilities: debugger tests, etc. """
import logging
import shutil
from abc import ABCMeta

from arangodb.installers.base import InstallerBase
from reporting.reporting_utils import step

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


class InstallerWin(InstallerBase, metaclass=ABCMeta):
    """inbetween class for windows specific utilities: debugger tests, etc."""

    @step
    def install_debug_package_impl(self):
        """unpack the archive with pdb files"""
        logging.info(f"Unpacking PDB files from package: {str(self.debug_package)}")

        extract_to = self.cfg.install_prefix / ".." / self.debug_package.replace(".zip", "")
        extract_to = extract_to.resolve()

        print("extracting: " + str(self.cfg.package_dir / self.debug_package) + " to " + str(extract_to))
        shutil.unpack_archive(
            str(self.cfg.package_dir / self.debug_package),
            str(extract_to),
        )
        logging.info("Unpacking successfull")
        self.cfg.debug_install_prefix = extract_to
        self.cfg.debug_package_is_installed = True
