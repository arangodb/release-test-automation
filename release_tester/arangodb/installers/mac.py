#!/usr/bin/env python3
""" run an installer for the debian based operating system """
import time
import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
import pexpect
import plistlib
from arangodb.log import ArangodLogExaminer
from arangodb.installers.base import InstallerBase
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerMac(InstallerBase):
    """ install .dmg's on a mac """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.installPrefix = None
        self.cfg.bin_dir = None
        self.cfg.sbin_dir = None
        self.cfg.localhost = 'localhost'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None
        self.mountpoint = None
        self.check_stripped = False
        self.check_symlink = True
        self.cfg.logDir = Path.home() / 'Library' / 'ArangoDB' / 'opt' / 'arangodb' / 'var' / 'log' / 'arangodb3'
        self.cfg.dbdir = Path.home() / 'Library' / 'ArangoDB' / 'opt' / 'arangodb' / 'var' / 'lib' / 'arangodb3'
        self.cfg.appdir = Path.home() / 'Library' / 'ArangoDB' / 'opt' / 'arangodb' / 'var' / 'lib' / 'arangodb3-apps'
        self.cfg.cfgdir = Path.home() / 'Library' / 'ArangoDB-etc' / 'arangodb3'

    def mountdmg(self, dmgpath):
        """
        Attempts to mount the dmg at dmgpath and returns first mountpoint
        """
        mountpoints = []
        dmgname = os.path.basename(dmgpath)
        cmd = ['/usr/bin/hdiutil', 'attach', str(dmgpath),
               '-mountRandom', '/tmp', '-nobrowse', '-plist',
               '-owners', 'on']
        print(cmd)
        proc = subprocess.Popen(cmd, bufsize=-1,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (pliststr, err) = proc.communicate()
        if proc.returncode:
            print('Error: "%s" while mounting %s.' % (err, dmgname),
                  file=sys.stderr)
            return None
        if pliststr:
            plist = plistlib.loads(pliststr)
            print(plist)
            for entity in plist['system-entities']:
                if 'mount-point' in entity:
                    mountpoints.append(entity['mount-point'])
        else:
            raise Exception("plist empty")
        return mountpoints[0]
    
    
    def unmountdmg(self, mountpoint):
        """
        Unmounts the dmg at mountpoint
        """
        proc = subprocess.Popen(['/usr/bin/hdiutil', 'detach', mountpoint],
                                bufsize=-1, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (dummy_output, err) = proc.communicate()
        if proc.returncode:
            print('Polite unmount failed: %s' % err, file=sys.stderr)
            print('Attempting to force unmount %s' % mountpoint, file=sys.stderr)
            # try forcing the unmount
            retcode = subprocess.call(['/usr/bin/hdiutil', 'detach', mountpoint,
                                       '-force'])
            if retcode:
                print('Failed to unmount %s' % mountpoint, file=sys.stderr)
    

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'x86_64'

        desc = {
            "ep"   : enterprise,
            "cfg"  : self.cfg.version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}-{cfg}.{arch}.dmg'.format(**desc)
        self.client_package = None
        self.debug_package = None

    def check_service_up(self):
        time.sleep(1)    # TODO
        return True

    def start_service(self):
        pass

    def stop_service(self):
        pass

    def upgrade_package(self):
        logging.info("upgrading Arangodb debian package")
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        server_upgrade = pexpect.spawnu('dpkg -i ' +
                                        str(self.cfg.package_dir / self.server_package))
        try:
            server_upgrade.expect('Upgrading database files')
            print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_upgrade.before)
            logging.info("X" * 80)
            logging.info("Upgrade failed!")
            sys.exit(1)
        try:
            logging.info("waiting for the upgrade to finish")
            server_upgrade.expect(pexpect.EOF, timeout=30)
            print(server_upgrade.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")

    def install_package(self):
        logging.info("Mounting DMG")
        self.mountpoint = self.mountdmg(self.cfg.package_dir / self.server_package)
        print(self.mountpoint)
        self.cfg.installPrefix = Path(self.mountpoint) / 'ArangoDB3-CLI.app' / 'Contents' / 'Resources'
        self.cfg.bin_dir = self.cfg.installPrefix
        self.cfg.sbin_dir = self.cfg.installPrefix
        self.cfg.real_bin_dir = self.cfg.installPrefix / 'opt' / 'arangodb' / 'bin'
        self.cfg.real_sbin_dir = self.cfg.installPrefix / 'opt' / 'arangodb' / 'sbin'
        self.cfg.all_instances = {
            'single': {
                'logfile': self.cfg.logDir / 'arangod.log'
            }
        }
        logging.info('Installation successfull')
        self.caclulate_file_locations()
        self.log_examiner = ArangodLogExaminer(self.cfg)
        self.log_examiner.detect_instance_pids()

    def un_install_package(self):
        uninstall = pexpect.spawnu('dpkg --purge ' +
                                   'arangodb3' +
                                   ('e' if self.cfg.enterprise else ''))

        try:
            uninstall.expect('Purging')
            print(uninstall.before)
            uninstall.expect(pexpect.EOF)
            print(uninstall.before)
        except pexpect.exceptions.EOF:
            print(uninstall.before)
            sys.exit(1)

    def cleanup_system(self):
        # TODO: should this be cleaned by the deb uninstall in first place?
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)
