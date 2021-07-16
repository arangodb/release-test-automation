#!/usr/bin/env python3
""" run an installer for the detected operating system """
import platform
import os
from pathlib import Path
from reporting.reporting_utils import step
import semver

# pylint: disable=R0903

class InstallerFrontend():
    """ class describing frontend instances """
    def __init__(self, proto: str, ip_address: str, port: int):
        self.proto = proto
        self.ip_address = ip_address
        self.port = port


class InstallerConfig():
    """ stores the baseline of this environment """
    # pylint: disable=R0913 disable=R0902
    def __init__(self,
                 version: str,
                 verbose: bool,
                 enterprise: bool,
                 encryption_at_rest: bool,
                 zip_package: bool,
                 package_dir: Path,
                 test_dir: Path,
                 mode: str,
                 publicip: str,
                 interactive: bool,
                 stress_upgrade: bool):
        self.publicip = publicip
        self.interactive = interactive
        self.enterprise = enterprise
        self.encryption_at_rest = encryption_at_rest and enterprise
        self.zip_package = zip_package

        self.mode = mode
        self.verbose = verbose
        self.package_dir = package_dir
        self.have_system_service = True
        self.have_debug_package = False
        self.stress_upgrade = stress_upgrade

        self.install_prefix = Path("/")

        self.base_test_dir = test_dir
        self.pwd = Path(os.path.dirname(os.path.realpath(__file__)))
        self.test_data_dir = self.pwd / '..' / '..' / '..' / 'test_data'

        self.username = "root"
        self.passvoid = ''
        self.jwt = ''

        self.port = 8529
        self.localhost = 'localhost'

        self.all_instances = {}
        self.frontends = []
        self.reset_version(version)
        self.log_dir = Path()
        self.bin_dir = Path()
        self.real_bin_dir = Path()
        self.sbin_dir = Path()
        self.real_sbin_dir = Path()
        self.dbdir = Path()
        self.appdir = Path()
        self.cfgdir = Path()
        winver = platform.win32_ver()

        self.hot_backup = (
            self.enterprise and
            (semver.compare(self.version, "3.5.1") >= 0) and
            not isinstance(winver, list)
        )
    def __repr__(self):
        return """
version: {0.version}
using enterpise: {0.enterprise}
using encryption at rest: {0.encryption_at_rest}
using zip: {0.zip_package}
package directory: {0.package_dir}
test directory: {0.base_test_dir}
mode: {0.mode}
public ip: {0.publicip}
interactive: {0.interactive}
verbose: {0.verbose}
""".format(self)

    def reset_version(self, version):
        """ establish a new version to manage """
        self.version = version
        self.semver = semver.VersionInfo.parse(version)

    @step("Add a frontend URL in components")
    def add_frontend(self, proto, ip_address, port):
        """ add a frontend URL in components """
        self.frontends.append(InstallerFrontend(proto, ip_address, port))

    @step("Set a frontend URL in components")
    def set_frontend(self, proto, ip_address, port):
        """ add a frontend URL in components """
        self.frontends = [InstallerFrontend(proto, ip_address, port)]

    @step("Generate a new password")
    def generate_password(self):
        """ generate a new password """
        raise NotImplementedError()
        #self.passvoid = 'cde'

    @step("Set directories")
    def set_directories(self, other):
        """ set all directories from the other object """
        if other.base_test_dir is None:
            raise Exception('base_test_dir: must not copy in None!')
        self.base_test_dir = other.base_test_dir
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
        if other.log_dir is None:
            raise Exception('log_dir: must not copy in None!')
        self.log_dir = other.log_dir
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
    # pylint: disable=too-many-return-statements
    """ detect the OS and its distro,
        choose the proper installer
        and return it"""
    winver = platform.win32_ver()
    if winver[0]:
        from arangodb.installers.nsis import InstallerW
        return InstallerW(install_config)

    macver = platform.mac_ver()
    if macver[0]:
        if install_config.zip_package:
            from arangodb.installers.tar import InstallerTAR
            return InstallerTAR(install_config)
        from arangodb.installers.mac import InstallerMac
        return InstallerMac(install_config)

    if platform.system() in [ "linux", "Linux" ]:
        import distro
        distro = distro.linux_distribution(full_distribution_name=False)
        if install_config.zip_package:
            from arangodb.installers.tar import InstallerTAR
            return InstallerTAR(install_config)
        if distro[0] in ['debian', 'ubuntu']:
            from arangodb.installers.deb import InstallerDeb
            return InstallerDeb(install_config)
        if distro[0] in ['centos', 'redhat', 'suse']:
            from arangodb.installers.rpm import InstallerRPM
            return InstallerRPM(install_config)
        if distro[0] in ['alpine']:
            from arangodb.installers.docker import InstallerDocker
            return InstallerDocker(install_config)
        raise Exception('unsupported linux distribution: ' + str(distro))
    raise Exception('unsupported os' + platform.system())


def create_config_installer_set(versions: list,
                                verbose: bool,
                                enterprise: bool,
                                encryption_at_rest: bool,
                                zip_package: bool,
                                package_dir: Path,
                                test_dir: Path,
                                mode: str,
                                publicip: str,
                                interactive: bool,
                                stress_upgrade: bool):
    """ creates sets of configs and installers """
    # pylint: disable=R0902 disable=R0913
    res = []
    for version in versions:
        print(version)
        install_config = InstallerConfig(version,
                                         verbose,
                                         enterprise,
                                         encryption_at_rest,
                                         zip_package,
                                         package_dir,
                                         test_dir,
                                         mode,
                                         publicip,
                                         interactive,
                                         stress_upgrade)
        installer = make_installer(install_config)
        res.append([install_config, installer])
    return res
