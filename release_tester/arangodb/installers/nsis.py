#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import shutil
import logging
from pathlib import Path
from pathlib import PureWindowsPath
import psutil
from arangodb.log import ArangodLogExaminer
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerW(InstallerBase):
    """ install the windows NSIS package """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.installPrefix = Path("C:/tmp")
        self.cfg.bin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.cfg.sbin_dir = self.cfg.installPrefix / "usr" / "bin"
        self.caclulate_file_locations()
        self.server_package = None
        self.client_package = None
        self.log_examiner = None
        self.service = None

    def check_symlink(self, file_to_check):
        return not file_to_check.is_symlink()

    def check_is_stripped(self, file_to_check, expect_stripped):
        pass # we don't do this on the wintendo.

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'win64'
        self.server_package = 'ArangoDB3%s-%s_%s.exe' % (
            enterprise,
            self.cfg.version,
            architecture)
        self.client_package = 'ArangoDB3%s-client_%s_%s.exe' % (
            enterprise,
            self.cfg.version,
            architecture)

    def install_package(self):
        self.cfg.logDir = self.cfg.installPrefix / "LOG"
        self.cfg.dbdir = self.cfg.installPrefix / "DB"
        self.cfg.appdir = self.cfg.installPrefix / "APP"
        self.cfg.installPrefix = self.cfg.installPrefix / "PROG"
        self.cfg.cfgdir = self.cfg.installPrefix / 'etc/arangodb3'
        cmd = [str(self.cfg.package_dir / self.server_package),
               '/PASSWORD=' + self.cfg.passvoid,
               '/INSTDIR=' + str(PureWindowsPath(self.cfg.installPrefix)),
               '/DATABASEDIR=' + str(PureWindowsPath(self.cfg.dbdir)),
               '/APPDIR=' + str(PureWindowsPath(self.cfg.appdir)),
               '/PATH=0',
               '/S',
               '/INSTALL_SCOPE_ALL=1']
        logging.info('running windows package installer:')
        logging.info(str(cmd))
        install = psutil.Popen(cmd)
        install.wait()
        self.service = psutil.win_service_get('ArangoDB')
        while not self.check_service_up():
            logging.info('starting...')
            time.sleep(1)
        self.enable_logging()
        self.stop_service()
        time.sleep(1)
        self.cfg.all_instances = {
            'single': {
                'logfile': self.cfg.logDir / 'arangod.log'
            }
        }
        self.log_examiner = ArangodLogExaminer(self.cfg)
        self.start_service()
        logging.info('Installation successfull')

    def getService(self):
        if self.service:
            return
        try:
            self.service = psutil.win_service_get('ArangoDB')
        except x as y:
            logging.error("failed to get service! - %s", str(x))
            raise x

    def un_install_package(self):
        # once we modify it, the uninstaller will leave it there...
        self.get_arangod_conf().unlink()
        uninstaller = "Uninstall.exe"
        tmp_uninstaller = Path("c:/tmp") / uninstaller
        # copy out the uninstaller as the windows facility would do:
        shutil.copyfile(self.cfg.installPrefix / uninstaller, tmp_uninstaller)

        cmd = [tmp_uninstaller,
               '/PURGE_DB=1',
               '/S',
               '_?=' + str(PureWindowsPath(self.cfg.installPrefix))]
        logging.info('running windows package uninstaller')
        logging.info(str(cmd))
        uninstall = psutil.Popen(cmd)
        uninstall.wait()
        shutil.rmtree(self.cfg.logDir)
        tmp_uninstaller.unlink()
        time.sleep(2)
        try:
            logging.info(psutil.win_service_get('ArangoDB'))
            self.getService()
            if self.service.status() != 'stopped':
                logging.info("service shouldn't exist anymore!")
        except:
            pass

    def check_service_up(self):
        self.getService()
        return self.service.status() == 'running'

    def start_service(self):
        self.getService()
        self.service.start()
        while self.service.status() != "running":
            logging.info(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own!"
                                "Configuration / Port problem?")
        self.log_examiner.detect_instance_pids()

    def stop_service(self):
        self.getService()
        self.service.stop()
        while self.service.status() != "stopped":
            logging.info(self.service.status())
            time.sleep(1)

    def cleanup_system(self):
        # TODO: should this be cleaned by the nsis uninstall in first place?
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
