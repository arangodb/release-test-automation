#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import shutil
import logging
import multiprocessing
from pathlib import Path
from pathlib import PureWindowsPath
import psutil
from arangodb.installers.base import InstallerBase

class InstallerW(InstallerBase):
    """ install the windows NSIS package """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, cfg):
        self.server_package = None
        self.client_package = None
        self.service = None
        self.remote_package_dir  = 'Windows'

        cfg.installPrefix = Path("C:/tmp")
        cfg.log_dir = cfg.installPrefix / "LOG"
        cfg.dbdir = cfg.installPrefix / "DB"
        cfg.appdir = cfg.installPrefix / "APP"
        cfg.installPrefix = cfg.installPrefix / ("PROG" + cfg.version)
        cfg.cfgdir = cfg.installPrefix / 'etc/arangodb3'

        cfg.bin_dir = cfg.installPrefix / "usr" / "bin"
        cfg.sbin_dir = cfg.installPrefix / "usr" / "bin"
        cfg.real_bin_dir = cfg.bin_dir
        cfg.real_sbin_dir = cfg.sbin_dir

        super().__init__(cfg)
        self.check_stripped = False
        self.check_symlink = False

    def supports_hot_backup(self):
        """ no hot backup support on the wintendo. """
        return False

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'win64'
        semdict = dict(self.cfg.semver.to_dict())
        if semdict['prerelease']:
            semdict['prerelease'] = '-{prerelease}'.format(**semdict)
        else:
            semdict['prerelease'] = ''
        version = '{major}.{minor}.{patch}{prerelease}'.format(**semdict)
        self.server_package = 'ArangoDB3%s-%s_%s.exe' % (
            enterprise,
            version,
            architecture)
        self.client_package = 'ArangoDB3%s-client-%s_%s.exe' % (
            enterprise,
            version,
            architecture)
        self.debug_package = None # TODO

    def upgrade_package(self, old_installer):
        self.stop_service()
        cmd = [str(self.cfg.package_dir / self.server_package),
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
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(60 / multiprocessing.cpu_count())
        self.set_system_instance()
        self.start_service()
        logging.info('Installation successfull')


    def install_package(self):
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
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(60 / multiprocessing.cpu_count())
        self.set_system_instance()
        self.start_service()
        logging.info('Installation successfull')

    def get_service(self):
        """ get a service handle """
        if self.service:
            return
        try:
            self.service = psutil.win_service_get('ArangoDB')
        except Exception as exc:
            logging.error("failed to get service! - %s", str(exc))
            return

    def un_install_package(self):
        # once we modify it, the uninstaller will leave it there...
        if self.get_arangod_conf().exists():
            self.get_arangod_conf().unlink()
        uninstaller = "Uninstall.exe"
        tmp_uninstaller = Path("c:/tmp") / uninstaller
        uninstaller = self.cfg.installPrefix / uninstaller

        if uninstaller.exists():
            # copy out the uninstaller as the windows facility would do:
            shutil.copyfile(uninstaller, tmp_uninstaller)

            cmd = [tmp_uninstaller,
                   '/PURGE_DB=1',
                   '/S',
                   '_?=' + str(PureWindowsPath(self.cfg.installPrefix))]
            logging.info('running windows package uninstaller')
            logging.info(str(cmd))
            uninstall = psutil.Popen(cmd)
            uninstall.wait()
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if tmp_uninstaller.exists():
            tmp_uninstaller.unlink()
        # the smaller the wintendo, the longer we shal let it rest,
        # since it needs to look at all these files we
        # just unloaded into it to make sure no harm originates from them.
        time.sleep(30 / multiprocessing.cpu_count())
        try:
            logging.info(psutil.win_service_get('ArangoDB'))
            self.get_service()
            if self.service and self.service.status() != 'stopped':
                logging.info("service shouldn't exist anymore!")
        except:
            pass

    def check_service_up(self):
        self.get_service()
        return self.service and self.service.status() == 'running'

    def start_service(self):
        self.get_service()
        if not self.service:
            logging.error("no service registered, not starting")
            return
        self.service.start()
        while self.service.status() != "running":
            logging.info(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own!"
                                "Configuration / Port problem?")
        # should be owned by init TODO wintendo what do you do here?
        self.instance.detect_pid(1)

    def stop_service(self):
        self.get_service()
        if not self.service:
            logging.error("no service registered, not stopping")
            return
        if self.service.status() != "stopped":
            self.service.stop()
        while self.service.status() != "stopped":
            logging.info(self.service.status())
            time.sleep(1)

    def cleanup_system(self):
        # TODO: should this be cleaned by the nsis uninstall in first place?
        if self.cfg.log_dir.exists():
            shutil.rmtree(self.cfg.log_dir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
