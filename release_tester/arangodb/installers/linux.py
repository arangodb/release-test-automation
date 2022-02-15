#!/usr/bin/env python3
""" inbetween class for linux specific utilities - GDB tests. """
import logging
import time

from reporting.reporting_utils import step
import pexpect
from arangodb.installers.base import InstallerBase
from tools.asciiprint import print_progress as progress

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


class InstallerLinux(InstallerBase):
    """inbetween class for linux specific utilities - GDB tests."""

    def __init__(self, cfg):
        self.remote_package_dir = "Linux"
        super().__init__(cfg)

    @step
    def gdb_test(self):
        """
        check that debug symbols for arangod binary are present
        """
        gdb = pexpect.spawnu("gdb " + str(self.cfg.real_sbin_dir / "arangod"))
        outputs = gdb.expect(
            [
                "Reading symbols from /usr/lib/debug/",
                "(No debugging symbols found in /usr/sbin/arangod)",
                "(gdb)",
            ]
        )
        if outputs in [0, 2]:
            logging.info("debugging symbol found")
            gdb.sendline("quit")
            logging.info("Quiting gdb session.")
            gdb.terminate(force=True)
        elif outputs in [1, 2]:
            logging.info("No debugging symbol found")
            gdb.sendline("quit")
            logging.info("Quiting gdb session.")
            gdb.terminate(force=True)
            raise Exception("GDB wasn't able to find debug symbols.")
        else:
            logging.info("Something wrong")
            raise Exception("Something went wrong during gdb test.")

    @step
    def check_service_up(self):
        if not self.instance:
            return False
        for count in range(20):
            if not self.instance.detect_gone():
                return True
            progress("SR" + str(count))
            time.sleep(1)
        return False
