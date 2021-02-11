#!/usr/bin/env python3
"""
 run an installer for the MacOS - heavily inspired by
     https://github.com/munki/macadmin-scripts
"""

import time
import os
import sys
import shutil
import logging
import subprocess
from pathlib import Path
import pexpect
import plistlib
from arangodb.instance import ArangodInstance
from arangodb.installers.base import InstallerBase
from tools.asciiprint import ascii_print
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallerMac(InstallerBase):
    """ install .dmg's on a mac """
    def __init__(self, cfg):
        self.remote_package_dir  = 'MacOSX'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.instance = None
        self.mountpoint = None
        self.check_stripped = True
        self.check_symlink = True
        self.basehomedir = Path.home() / 'Library' / 'ArangoDB'
        self.baseetcdir = Path.home() / 'Library' / 'ArangoDB-etc'

        cfg.installPrefix = None
        cfg.localhost = 'localhost'
        cfg.passvoid = '' # default mac install doesn't set passvoid

        cfg.logDir = self.basehomedir / 'opt' / 'arangodb' / 'var' / 'log' / 'arangodb3'
        cfg.dbdir = self.basehomedir / 'opt' / 'arangodb' / 'var' / 'lib' / 'arangodb3'
        cfg.appdir = self.basehomedir / 'opt' / 'arangodb' / 'var' / 'lib' / 'arangodb3-apps'
        cfg.cfgdir = self.baseetcdir
        cfg.pidfile = Path("/var/tmp/arangod.pid")

        # we gonna override them to their real locations later on.
        cfg.bin_dir = Path('/')
        cfg.sbin_dir = Path('/')
        cfg.real_bin_dir = Path('/')
        cfg.real_sbin_dir = Path('/')

        super().__init__(cfg)


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
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                stdin=subprocess.PIPE)
        proc.stdin.write(b"y\n") # answer 'Agree Y/N?' the dumb way...
        (pliststr, err) = proc.communicate()
        # print(str(pliststr))

        offset = pliststr.find(b'<?xml version="1.0" encoding="UTF-8"?>')
        if offset > 0:
            print('got string')
            print(offset)
            ascii_print(str(pliststr[0:offset]))
            pliststr = pliststr[offset:]

        if proc.returncode:
            logging.error('while mounting')
            return None
        if pliststr:
            # pliststr = bytearray(pliststr, 'ascii')
            # print(pliststr)
            plist = plistlib.loads(pliststr)
            print(plist)
            for entity in plist['system-entities']:
                if 'mount-point' in entity:
                    mountpoints.append(entity['mount-point'])
        else:
            raise Exception("plist empty")
        return mountpoints[0]

    def detect_dmg_mountpoints(self, dmgpath):
        """
        Unmounts the dmg at mountpoint
        """
        mountpoints = []
        dmgname = os.path.basename(dmgpath)
        cmd = ['/usr/bin/hdiutil', 'info', '-plist']
        proc = subprocess.Popen(cmd, bufsize=-1,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (pliststr, err) = proc.communicate()
        if proc.returncode:
            logging.error('Error: "%s" while listing mountpoints %s.' % (err, dmgpath))
            return mountpoints
        if pliststr:
            plist = plistlib.loads(pliststr)
            for entity in plist['images']:
                if ('image-path' not in entity or
                    entity['image-path'].find(str(dmgpath)) < 0):
                    continue
                if 'system-entities' in entity:
                    for item in entity['system-entities']:
                        if 'mount-point' in item:
                            mountpoints.append(item['mount-point'])
        else:
            raise Exception("plist empty")
        return mountpoints

    def unmountdmg(self, mountpoint):
        """
        Unmounts the dmg at mountpoint
        """
        logging.info("unmounting %s", mountpoint)
        proc = subprocess.Popen(['/usr/bin/hdiutil', 'detach', mountpoint],
                                 bufsize=-1, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE)
        (dummy_output, err) = proc.communicate()
        if proc.returncode:
            logging.error('Polite unmount failed: %s' % err)
            logging.error('Attempting to force unmount %s' % mountpoint)
            # try forcing the unmount
            retcode = subprocess.call(['/usr/bin/hdiutil', 'detach', mountpoint, '-force'])
            if retcode:
                logging.error('while mounting')

    
    def run_installer_script(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        script = Path(self.mountpoint) / 'ArangoDB3{}-CLI.app'.format(enterprise) / 'Contents' / 'MacOS' / 'ArangoDB3-CLI'
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
        enterprise = 'e' if self.cfg.enterprise else ''
        architecture = 'x86_64'

        semdict = dict(self.cfg.semver.to_dict())
        if semdict['prerelease']:
            semdict['prerelease'] = '-{prerelease}'.format(**semdict)
        else:
            semdict['prerelease'] = ''
        version = '{major}.{minor}.{patch}{prerelease}'.format(**semdict)

        desc = {
            "ep"   : enterprise,
            "cfg"  : version,
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
        self.instance.terminate_instance()

    def upgrade_package(self, old_installer):
        os.environ["UPGRADE_DB"] = "No"
        self.install_package()

    def un_install_package_for_upgrade(self):
        """ hook to uninstall old package for upgrade """
        # self.un_install_package()

    def install_package(self):
        if self.cfg.pidfile.exists():
            self.cfg.pidfile.unlink()
        logging.info("Mounting DMG")
        self.mountpoint = self.mountdmg(self.cfg.package_dir / self.server_package)
        print(self.mountpoint)
        enterprise = 'e' if self.cfg.enterprise else ''
        self.cfg.installPrefix = Path(self.mountpoint) / 'ArangoDB3{}-CLI.app'.format(enterprise) / 'Contents' / 'Resources'
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
        self.run_installer_script()
        self.instance = ArangodInstance("single", "8529", self.cfg.localhost, self.cfg.publicip, self.cfg.logDir)
        self.instance.detect_pid(1) # should be owned by init - TODO

    def un_install_package(self):
        self.stop_service()
        if not self.mountpoint:
            mpts = self.detect_dmg_mountpoints(self.cfg.package_dir / self.server_package)
            for mountpoint in mpts:
                self.unmountdmg(mountpoint)
        else:
            self.unmountdmg(self.mountpoint)

    def cleanup_system(self): 
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
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
