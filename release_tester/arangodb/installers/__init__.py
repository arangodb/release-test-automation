#!/usr/bin/env python3
""" run an installer for the detected operating system """
import platform
import os
from pathlib import Path
import semver

class InstallerFrontend():
    def __init__(self, proto: str, ip: str, port: int):
        self.proto = proto
        self.ip = ip
        self.port = port


class InstallerConfig():
    """ stores the baseline of this environment """
    def __init__(self,
                 version: str,
                 verbose: bool,
                 enterprise: bool,
                 zip: bool,
                 package_dir: Path,
                 mode: str,
                 publicip: str,
                 interactive: bool):
        self.publicip = publicip
        self.interactive = interactive
        self.enterprise = enterprise
        self.zip = zip

        self.mode = mode
        self.version = version
        self.semver = semver.VersionInfo.parse(version)
        self.verbose = verbose
        self.package_dir = package_dir
        self.have_system_service = True
        self.have_debug_package = False

        self.install_prefix = Path("/")
        self.pwd = Path(os.path.dirname(os.path.realpath(__file__)))
        self.test_data_dir = self.pwd / '..' / '..' / '..' / 'test_data'
        self.cfgdir = Path('.')
        self.username = "root"
        self.passvoid = ''
        self.jwt = ''

        self.port = 8529
        self.localhost = 'localhost'

        self.all_instances = {}
        self.frontends = []

    def add_frontend(self, proto, ip, port):
        """ add a frontend URL in components """
        self.frontends.append(InstallerFrontend(proto, ip, port))

    def set_frontend(self, proto, ip, port):
        """ add a frontend URL in components """
        self.frontends = [InstallerFrontend(proto, ip, port)]

    def generate_password(self):
        """ generate a new password """
        raise NotImplementedError()
        #self.passvoid = 'cde'

    def set_directories(self, other):
        """ set all directories from the other object """
        if other.bin_dir is None:
            raise Exception('bin_dir: must not copy in None!')
        self.bin_dir = other.bin_dir
        if other.sbin_dir is None:
            raise Exception('sbin_dir: must not copy in None!')
        self.sbin_dir = other.sbin_dir
        if other.real_bin_dir is None:
            raise Exception('real_bin_dir: must not copy in None!')
        self.real_bin_dir = other.real_bin_dir
        if other.real_sbin_dir is None:
            raise Exception('real_sbin_dir: must not copy in None!')
        self.real_sbin_dir = other.real_sbin_dir
        if other.logDir is None:
            raise Exception('logDir: must not copy in None!')
        self.logDir = other.logDir
        if other.dbdir is None:
            raise Exception('dbdir: must not copy in None!')
        self.dbdir = other.dbdir
        if other.appdir is None:
            raise Exception('appdir: must not copy in None!')
        self.appdir = other.appdir
        if other.cfgdir is None:
            raise Exception('cfgdir: must not copy in None!')
        self.cfgdir = other.cfgdir
        if other.install_prefix is None:
            raise Exception('install_prefix: must not copy in None!')
        self.install_prefix = other.install_prefix

#pylint: disable=import-outside-toplevel
def make_installer(install_config: InstallerConfig):
    """ detect the OS and its distro,
        choose the proper installer
        and return it"""
    winver = platform.win32_ver()
    if winver[0]:
        from arangodb.installers.nsis import InstallerW
        return InstallerW(install_config)

    import resource
    nofd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    if nofd < 10000:
        raise Exception("please use ulimit -n <count>"
                        " to adjust the number of allowed filedescriptors"
                        " to a value greater or eqaul 10000."
                        " Currently you have set the limit to: " + str(nofd))

    macver = platform.mac_ver()
    if macver[0]:
        if install_config.zip:
            from arangodb.installers.tar import InstallerTAR
            return InstallerTAR(install_config)
        else:
            from arangodb.installers.mac import InstallerMac
            return InstallerMac(install_config)

    elif platform.system() in [ "linux", "Linux" ]:
        import distro
        distro = distro.linux_distribution(full_distribution_name=False)
        if install_config.zip:
            from arangodb.installers.tar import InstallerTAR
            return InstallerTAR(install_config)
        elif distro[0] in ['debian', 'ubuntu']:
            from arangodb.installers.deb import InstallerDeb
            return InstallerDeb(install_config)
        elif distro[0] in ['centos', 'redhat', 'suse']:
            from arangodb.installers.rpm import InstallerRPM
            return InstallerRPM(install_config)
        raise Exception('unsupported linux distribution: ' + distro)
    raise Exception('unsupported os' + platform.system())

def make_source_installer(install_config: InstallerConfig):
    from arangodb.installers.source import InstallerSRC
    return InstallerSRC(install_config)
