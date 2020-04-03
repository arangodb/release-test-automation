#!/usr/bin/env python3
""" run an installer for the detected operating system """
import time
import os
import sys
import re
import shutil
import platform
import logging
from pathlib import Path
from abc import abstractmethod, ABC
import yaml
import psutil
from installers import arangosh
import installers.arangodlog as arangodlog

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class InstallConfig():
    """ stores the baseline of this environment """
    def __init__(self, version, enterprise, package_dir, publicip):
        self.publicip = publicip
        self.username = "root"
        self.passvoid = "abc"
        self.enterprise = enterprise
        self.version = version
        self.package_dir = package_dir
        self.install_prefix = Path("/")
        self.jwt = ''
        self.port = 8529
        self.localhost = 'localhost'
        self.all_instances = {}

    def generate_password(self):
        """ generate a new password """
        self.passvoid = 'cde'


class InstallerBase(ABC):
    """ this is the prototype for the operation system agnostic installers """
    @abstractmethod
    def calculate_package_names(self):
        """ which filenames will we be able to handle"""

    @abstractmethod
    def install_package(self):
        """ install the packages to the system """

    @abstractmethod
    def un_install_package(self):
        """ remove the installed packages from the system """

    @abstractmethod
    def check_service_up(self):
        """ check whether the system arangod service is running """

    @abstractmethod
    def start_service(self):
        """ launch the arangod system service """

    @abstractmethod
    def stop_service(self):
        """ stop the arangod system service """

    @abstractmethod
    def cleanup_system(self):
        """ if the packages are known to not properly cleanup - do it here. """

    def get_arangod_conf(self):
        """ where on the disk is the arangod config installed? """
        return self.cfg.cfgdir / 'arangod.conf'

    def calc_config_file_name(self):
        """ store our config to disk - so we can be invoked partly """
        cfg_file = Path()
        if self.cfg.install_prefix == Path('/'):
            cfg_file = Path('/') / 'tmp' / 'config.yml'
        else:
            cfg_file = Path('c:') / 'tmp' / 'config.yml'
        return cfg_file

    def save_config(self):
        """ dump the config to disk """
        self.calc_config_file_name().write_text(yaml.dump(self.cfg))

    def load_config(self):
        """ deserialize the config from disk """
        with open(self.calc_config_file_name()) as fileh:
            self.cfg = yaml.load(fileh, Loader=yaml.Loader)
        self.log_examiner = arangodlog.ArangodLogExaminer(self.cfg)

    def broadcast_bind(self):
        """
        modify the arangod.conf so the system will broadcast bind
        so you can access the SUT from the outside
        with your local browser
        """
        arangodconf = self.get_arangod_conf().read_text()
        iprx = re.compile('127\\.0\\.0\\.1')
        new_arangod_conf = iprx.subn('0.0.0.0', arangodconf)
        self.get_arangod_conf().write_text(new_arangod_conf[0])
        logging.info("arangod now configured for broadcast bind")

    def enable_logging(self):
        """ if the packaging doesn't enable logging,
            do it using this function """
        arangodconf = self.get_arangod_conf().read_text()
        self.cfg.logDir.mkdir(parents=True)
        new_arangod_conf = arangodconf.replace('[log]',
                                               '[log]\nfile = ' +
                                               str(self.cfg.logDir / 'arangod.log'))
        print(new_arangod_conf)
        self.get_arangod_conf().write_text(new_arangod_conf[0])
        logging.info("arangod now configured for logging")

    def check_installed_paths(self):
        """ check whether the requested directories and files were created """
        if (
                not self.cfg.dbdir.is_dir() or
                not self.cfg.appdir.is_dir() or
                not self.cfg.cfgdir.is_dir()
        ):
            raise Exception("expected installation paths are not there")

        if not self.get_arangod_conf().is_file():
            raise Exception("configuration files aren't there")

    def check_engine_file(self):
        """ check for the engine file to test whether the DB was created """
        if not Path(self.cfg.dbdir / 'ENGINE').is_file():
            raise Exception("database engine file not there!")

    def check_uninstall_cleanup(self):
        """ check whether all is gone after the uninstallation """
        success = True

        if (self.cfg.installPrefix != Path("/") and
                self.cfg.installPrefix.is_dir()):
            logging.info("Path not removed: %s", str(self.cfg.installPrefix))
            success = False
        if os.path.exists(self.cfg.appdir):
            logging.info("Path not removed: %s", str(self.cfg.appdir))
            success = False
        if os.path.exists(self.cfg.dbdir):
            logging.info("Path not removed: %s", str(self.cfg.dbdir))
            success = False
        return success


class InstallerDeb(InstallerBase):
    """ install .deb's on debian or ubuntu hosts """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.localhost = 'ip6-localhost'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        package_version = '1'
        architecture = 'amd64'

        desc = {
            "ep"   : enterprise,
            "cfg"  : self.cfg.version,
            "ver"  : package_version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.client_package = 'arangodb3{ep}-client_{cfg}-{ver}_{arch}.deb'.format(**desc)
        self.debug_package = 'arangodb3{ep}-dbg_{cfg}-{ver}_{arch}.deb'.format(**desc)

    def check_service_up(self):
        time.sleep(1)    # TODO

    def start_service(self):
        import pexpect
        startserver = pexpect.spawnu('service arangodb3 start')
        logging.info("waiting for eof")
        startserver.expect(pexpect.EOF, timeout=30)
        while startserver.isalive():
            logging.info('.')
            if startserver.exitstatus != 0:
                raise Exception("server service start didn't"
                                "finish successfully!")
        time.sleep(0.1)
        self.log_examiner.detect_instance_pids()

    def stop_service(self):
        import pexpect
        stopserver = pexpect.spawnu('service arangodb3 stop')
        logging.info("waiting for eof")
        stopserver.expect(pexpect.EOF, timeout=30)
        while stopserver.isalive():
            logging.info('.')
            if stopserver.exitstatus != 0:
                raise Exception("server service stop didn't"
                                "finish successfully!")

    def install_package(self):
        import pexpect
        self.cfg.installPrefix = Path("/")
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')
        self.cfg.all_instances = {
            'single': {
                'logfile': self.cfg.installPrefix / self.cfg.logDir / 'arangod.log'
            }
        }
        logging.info("installing Arangodb debian package")
        os.environ['DEBIAN_FRONTEND'] = 'readline'
        server_install = pexpect.spawnu('dpkg -i ' +
                                        str(self.cfg.package_dir / self.server_package))
        try:
            server_install.expect('user:')
            print(server_install.before)
            server_install.sendline(self.cfg.passvoid)
            server_install.expect('user:')
            print(server_install.before)
            server_install.sendline(self.cfg.passvoid)
            server_install.expect("Automatically upgrade database files")
            print(server_install.before)
            server_install.sendline("yes")
            server_install.expect("Database storage engine")
            print(server_install.before)
            server_install.sendline("1")
            server_install.expect("Backup database files before upgrading")
            print(server_install.before)
            server_install.sendline("no")
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_install.before)
            logging.info("X" * 80)
            logging.info("Installation failed!")
            sys.exit(1)
        try:
            logging.info("waiting for the installation to finish")
            server_install.expect(pexpect.EOF, timeout=30)
            print(server_install.before)
        except pexpect.exceptions.EOF:
            logging.info("TIMEOUT!")
        while server_install.isalive():
            logging.info('.')
            if server_install.exitstatus != 0:
                raise Exception("server installation didn't finish successfully!")
        logging.info('Installation successfull')
        self.log_examiner = arangodlog.ArangodLogExaminer(self.cfg)
        self.log_examiner.detect_instance_pids()

    def un_install_package(self):
        import pexpect
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


class InstallerRPM(InstallerBase):
    """ install .rpm's on RedHat, Centos or SuSe systems """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.baseTestDir = Path('/tmp')
        self.cfg.localhost = 'localhost6'
        self.server_package = None
        self.client_package = None
        self.debug_package = None
        self.log_examiner = None

    def calculate_package_names(self):
        enterprise = 'e' if self.cfg.enterprise else ''
        package_version = '1.0'
        architecture = 'x86_64'

        desc = {
            "ep"   : enterprise,
            "cfg"  : self.cfg.version,
            "ver"  : package_version,
            "arch" : architecture
        }

        self.server_package = 'arangodb3{ep}-{cfg}-{ver}.{arch}.rpm'.format(**desc)
        self.client_package = 'arangodb3{ep}-client-{cfg}-{ver}.{arch}.rpm'.format(**desc)
        self.debug_package = 'arangodb3{ep}-debuginfo-{cfg}-{ver}.{arch}.rpm'.format(**desc)

    def check_service_up(self):
        if 'PID' in self.cfg.all_instances['single']:
            try:
                psutil.Process(self.cfg.all_instances.single['PID'])
            except:
                return False
        else:
            return False
        time.sleep(1)   # TODO
        return True

    def start_service(self):
        startserver = psutil.Popen(['service', 'arangodb3', 'start'])
        logging.info("waiting for eof")
        startserver.wait()
        time.sleep(0.1)
        self.log_examiner.detect_instance_pids()

    def stop_service(self):
        stopserver = psutil.Popen(['service', 'arangodb3', 'stop'])
        logging.info("waiting for eof")
        stopserver.wait()
        while self.check_service_up():
            time.sleep(1)

    def install_package(self):
        import pexpect
        self.cfg.installPrefix = Path("/")
        self.cfg.logDir = Path('/var/log/arangodb3')
        self.cfg.dbdir = Path('/var/lib/arangodb3')
        self.cfg.appdir = Path('/var/lib/arangodb3-apps')
        self.cfg.cfgdir = Path('/etc/arangodb3')
        self.cfg.all_instances = {
            'single': {
                'logfile': self.cfg.installPrefix /
                self.cfg.logDir / 'arangod.log'
            }
        }
        self.log_examiner = arangodlog.ArangodLogExaminer(self.cfg)
        logging.info("installing Arangodb RPM package")
        package = self.cfg.package_dir / self.server_package
        if not package.is_file():
            logging.info("package doesn't exist: %s", str(package))
            raise Exception("failed to find package")

        logging.info("-"*80)
        server_install = pexpect.spawnu('rpm ' + '-i ' + str(package))
        reply = None
        try:
            server_install.expect('the current password is')
            print(server_install.before)
            server_install.expect(pexpect.EOF, timeout=30)
            reply = server_install.before
            print(reply)
            logging.info("-"*80)
        except pexpect.exceptions.EOF:
            logging.info("X" * 80)
            print(server_install.before)
            logging.info("X" * 80)
            logging.info("Installation failed!")
            sys.exit(1)
        start = reply.find("'")
        end = reply.find("'", start + 1)
        self.cfg.passvoid = reply[start + 1: end]
        self.start_service()
        self.log_examiner.detect_instance_pids()
        pwcheckarangosh = arangosh.ArangoshExecutor(self.cfg)
        if not pwcheckarangosh.js_version_check():
            logging.info(
                "Version Check failed -"
                "probably setting the default random password didn't work! %s",
                self.cfg.passvoid)
        self.stop_service()
        self.cfg.passvoid = "sanoetuh"   # TODO
        etpw = pexpect.spawnu('/usr/sbin/arango-secure-installation')
        try:
            etpw.expect('Please enter a new password'
                        ' for the ArangoDB root user:')
            etpw.sendline(self.cfg.passvoid)
            etpw.expect('Repeat password:')
            etpw.sendline(self.cfg.passvoid)
            etpw.expect(pexpect.EOF)
        except pexpect.exceptions.EOF:
            logging.info("setting our password failed!")
            logging.info("X" * 80)
            print(etpw.before)
            logging.info("X" * 80)
            sys.exit(1)
        self.start_service()
        self.log_examiner.detect_instance_pids()

    def un_install_package(self):
        uninstall = psutil.Popen(['rpm', '-e', 'arangodb3' +
                                  ('e' if self.cfg.enterprise else '')])
        uninstall.wait()

    def cleanup_system(self):
        # TODO: should this be cleaned by the rpm uninstall in first place?
        if self.cfg.logDir.exists():
            shutil.rmtree(self.cfg.logDir)
        if self.cfg.dbdir.exists():
            shutil.rmtree(self.cfg.dbdir)
        if self.cfg.appdir.exists():
            shutil.rmtree(self.cfg.appdir)
        if self.cfg.cfgdir.exists():
            shutil.rmtree(self.cfg.cfgdir)


class InstallerW(InstallerBase):
    """ install the windows NSIS package """
    def __init__(self, install_config):
        self.cfg = install_config
        self.cfg.installPrefix = Path("C:/tmp")
        self.cfg.baseTestDir = Path('/tmp')
        self.server_package = None
        self.client_package = None
        self.log_examiner = None
        self.service = None

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
        from pathlib import PureWindowsPath
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
        self.log_examiner = arangodlog.ArangodLogExaminer(self.cfg)
        self.start_service()
        logging.info('Installation successfull')

    def un_install_package(self):
        from pathlib import PureWindowsPath
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
            service = psutil.win_service_get('ArangoDB')
            if service.status() != 'stopped':
                logging.info("service shouldn't exist anymore!")
        except:
            pass

    def check_service_up(self):
        return self.service.status() == 'running'

    def start_service(self):
        self.service.start()
        while self.service.status() != "running":
            logging.info(self.service.status())
            time.sleep(1)
            if self.service.status() == "stopped":
                raise Exception("arangod service stopped again on its own!"
                                "Configuration / Port problem?")
        self.log_examiner.detect_instance_pids()

    def stop_service(self):
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


def get(*args, **kwargs):
    """ detect the OS and its distro, choose the proper installer and return it"""
    winver = platform.win32_ver()
    if winver[0]:
        return InstallerW(InstallConfig(*args, **kwargs))
    macver = platform.mac_ver()
    if macver[0]:
        raise Exception("mac not yet implemented")

    if platform.system() == "linux" or platform.system() == "Linux":
        import distro
        distro = distro.linux_distribution(full_distribution_name=False)

        if distro[0] in ['debian', 'ubuntu']:
            return InstallerDeb(InstallConfig(*args, **kwargs))
        if distro[0] in ['centos', 'redhat', 'suse']:
            return InstallerRPM(InstallConfig(*args, **kwargs))
        raise Exception('unsupported linux distribution: ' + distro)
    raise Exception('unsupported os' + platform.system())
