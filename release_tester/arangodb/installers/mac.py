#!/usr/bin/env python3
"""
 run an installer for the MacOS - heavily inspired by
     https://github.com/munki/macadmin-scripts
"""

import time
import os
import shutil
import logging
import subprocess
from pathlib import Path
import plistlib

import psutil

from reporting.reporting_utils import step
import pexpect
from allure_commons._allure import attach

from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print
from tools.asciiprint import print_progress as progress

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")


@step
def _mountdmg(dmgpath):
    """
    Attempts to mount the dmg at dmgpath and returns first mountpoint
    """
    mountpoints = []
    cmd = [
        "/usr/bin/hdiutil",
        "attach",
        str(dmgpath),
        "-mountRandom",
        "/tmp",
        "-nobrowse",
        "-plist",
        "-owners",
        "on",
    ]
    print(cmd)
    pliststr = ""
    with subprocess.Popen(
        cmd,
        bufsize=-1,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE,
    ) as proc:
        proc.stdin.write(b"y\n")  # answer 'Agree Y/N?' the dumb way...
        # pylint: disable=unused-variable
        (pliststr, _) = proc.communicate()

    offset = pliststr.find(b'<?xml version="1.0" encoding="UTF-8"?>')
    if offset > 0:
        print("got string")
        print(offset)
        ascii_print(str(pliststr[0:offset]))
        pliststr = pliststr[offset:]

    if proc.returncode:
        logging.error("while mounting")
        return None
    if pliststr:
        # pliststr = bytearray(pliststr, 'ascii')
        # print(pliststr)
        plist = plistlib.loads(pliststr)
        print(plist)
        for entity in plist["system-entities"]:
            if "mount-point" in entity:
                mountpoints.append(entity["mount-point"])
    else:
        raise Exception("plist empty")
    return mountpoints[0]


@step
def _detect_dmg_mountpoints(dmgpath):
    """
    Unmounts the dmg at mountpoint
    """
    mountpoints = []
    cmd = ["/usr/bin/hdiutil", "info", "-plist"]
    pliststr = ""
    err = ""
    with subprocess.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
        (pliststr, err) = proc.communicate()
        if proc.returncode:
            logging.error('Error: "%s" while listing mountpoints %s.' % (err, dmgpath))
            return mountpoints
    if pliststr:
        plist = plistlib.loads(pliststr)
        for entity in plist["images"]:
            if "image-path" not in entity or entity["image-path"].find(str(dmgpath)) < 0:
                continue
            if "system-entities" in entity:
                for item in entity["system-entities"]:
                    if "mount-point" in item:
                        mountpoints.append(item["mount-point"])
    else:
        raise Exception("plist empty")
    attach(mountpoints)
    return mountpoints


def _unmountdmg(mountpoint):
    """
    Unmounts the dmg at mountpoint
    """
    logging.info("unmounting %s", mountpoint)
    with subprocess.Popen(
        ["/usr/bin/hdiutil", "detach", mountpoint],
        bufsize=-1,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        (_, err) = proc.communicate()
        if proc.returncode:
            logging.error("Polite unmount failed: %s" % err)
            logging.error("Attempting to force unmount %s" % mountpoint)
            # try forcing the unmount
            retcode = subprocess.call(["/usr/bin/hdiutil", "detach", mountpoint, "-force"])
            if retcode:
                logging.error("while mounting")


class InstallerMac(InstallerBase):
    """install .dmg's on a mac"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    def __init__(self, cfg):
        self.remote_package_dir = "MacOSX"
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.instance = None
        self.mountpoint = None
        self.basehomedir = Path.home() / "Library" / "ArangoDB"
        self.baseetcdir = Path.home() / "Library" / "ArangoDB-etc"
        self.installer_type = "DMG"

        cfg.install_prefix = Path("/")
        cfg.localhost = "localhost"
        cfg.passvoid = ""  # default mac install doesn't set passvoid

        cfg.log_dir = self.basehomedir / "opt" / "arangodb" / "var" / "log" / "arangodb3"
        cfg.dbdir = self.basehomedir / "opt" / "arangodb" / "var" / "lib" / "arangodb3"
        cfg.appdir = self.basehomedir / "opt" / "arangodb" / "var" / "lib" / "arangodb3-apps"
        cfg.cfgdir = self.baseetcdir
        cfg.pidfile = Path("/var/tmp/arangod.pid")

        # we gonna override them to their real locations later on.
        cfg.bin_dir = Path("/")
        cfg.sbin_dir = Path("/")
        cfg.real_bin_dir = Path("/")
        cfg.real_sbin_dir = Path("/")

        super().__init__(cfg)
        self.check_stripped = False
        self.check_notarized = True

    @step
    def run_installer_script(self):
        """this will run the installer script from the dmg"""
        enterprise = "e" if self.cfg.enterprise else ""
        script = (
            Path(self.mountpoint) / "ArangoDB3{}-CLI.app".format(enterprise) / "Contents" / "MacOS" / "ArangoDB3-CLI"
        )
        print(script)
        os.environ["STORAGE_ENGINE"] = "auto"
        installscript = pexpect.spawnu(str(script))
        try:
            installscript.expect("is ready for business. Have fun!", timeout=60)
            ascii_print(installscript.before)
        except pexpect.exceptions.EOF:
            ascii_print(installscript.before)
        installscript.kill(0)

    def calculate_package_names(self):
        enterprise = "e" if self.cfg.enterprise else ""
        architecture = "x86_64" if self.machine == "x86_64" else "arm64"

        prerelease = self.cfg.semver.prerelease
        semdict = dict(self.cfg.semver.to_dict())
        if semdict["build"] is None:
            semdict["build"] = ""
        if prerelease is None or prerelease == "":
            semdict["prerelease"] = ""
        elif prerelease == "nightly":
            semdict["prerelease"] = ".{prerelease}".format(**semdict)
        elif prerelease.startswith("alpha"):
            semdict["prerelease"] = "." + semdict["prerelease"].replace(".", "")
        elif prerelease.startswith("beta"):
            semdict["prerelease"] = "." + semdict["prerelease"].replace(".", "")
        elif prerelease.startswith("rc"):
            semdict["prerelease"] = "-" + semdict["prerelease"].replace("rc", "rc.")
        elif len(prerelease) > 0:
            semdict["build"] = "." + semdict["prerelease"]
            semdict["prerelease"] = ""

        version = "{major}.{minor}.{patch}{build}{prerelease}".format(**semdict)

        desc = {"ep": enterprise, "cfg": version, "arch": architecture}

        self.server_package = "arangodb3{ep}-{cfg}.{arch}.dmg".format(**desc)
        self.client_package = None
        self.debug_package = None

    @step
    def check_service_up(self):
        for count in range(30):
            if not self.instance.detect_gone():
                return True
            progress("SR" + str(count))
            time.sleep(1)
        return False

    def start_service(self):
        """there is no system way, hence do it manual:"""
        if self.check_service_up():
            print("already running, doing nothing.")
        arangod = self.cfg.real_sbin_dir / "arangod"
        system_cmd = [
            str(arangod),
            "-c",
            self.baseetcdir / "arangod.conf",
            "--daemon",
            "--pid-file",
            "/var/tmp/arangod.pid",
        ]
        print("Launching: " + str(system_cmd))
        ret = psutil.Popen(system_cmd).wait()
        print("started system arangod: " + str(ret))
        self.instance.detect_pid(1)

    @step
    def stop_service(self):
        """ stop the system wide service """
        self.instance.terminate_instance()

    @step
    def upgrade_server_package(self, old_installer):
        """ upgrade an existing installation. """
        os.environ["UPGRADE_DB"] = "Yes"
        self.instance = old_installer.instance
        self.stop_service()
        self.install_server_package_backend()
        os.unsetenv("UPGRADE_DB")

    @step
    def install_server_package_impl(self):
        """ fresh install """
        self.install_server_package_backend()

    def install_server_package_backend(self):
        """ install or upgrade """
        if self.cfg.pidfile.exists():
            self.cfg.pidfile.unlink()
        logging.info("Mounting DMG")
        self.mountpoint = _mountdmg(self.cfg.package_dir / self.server_package)
        print(self.mountpoint)
        enterprise = "e" if self.cfg.enterprise else ""
        self.cfg.install_prefix = (
            Path(self.mountpoint) / "ArangoDB3{}-CLI.app".format(enterprise) / "Contents" / "Resources"
        )
        self.cfg.bin_dir = self.cfg.install_prefix
        self.cfg.sbin_dir = self.cfg.install_prefix
        self.cfg.real_bin_dir = self.cfg.install_prefix / "opt" / "arangodb" / "bin"
        self.cfg.real_sbin_dir = self.cfg.install_prefix / "opt" / "arangodb" / "sbin"
        self.cfg.all_instances = {"single": {"logfile": self.cfg.log_dir / "arangod.log"}}
        logging.info("Installation successfull")
        self.calculate_file_locations()
        self.run_installer_script()
        self.set_system_instance()
        self.instance.detect_pid(1)

    @step
    def un_install_server_package_impl(self):
        """ remove the package """
        self.stop_service()
        if not self.mountpoint:
            mpts = _detect_dmg_mountpoints(self.cfg.package_dir / self.server_package)
            for mountpoint in mpts:
                _unmountdmg(mountpoint)
        else:
            _unmountdmg(self.mountpoint)

    def install_client_package_impl(self):
        """ no mac client package """

    def  un_install_client_package_impl(self):
        """ no mac client package """

    @step
    def cleanup_system(self):
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
        if self.baseetcdir.exists():
            shutil.rmtree(self.baseetcdir)
        if self.basehomedir.exists():
            shutil.rmtree(self.basehomedir)
