#!/usr/bin/env python3
""" run an installer for the detected operating system """
from enum import Enum
import platform
import os
from pathlib import Path
from reporting.reporting_utils import step
import semver
# pylint: disable=R0903


class HotBackupSetting(Enum):
    """whether we want thot backup or not"""

    DISABLED = 0
    DIRECTORY = 1
    S3BUCKET = 2


hb_strings = {
    HotBackupSetting.DISABLED: "disabled",
    HotBackupSetting.DIRECTORY: "directory",
    HotBackupSetting.S3BUCKET: "s3bucket",
}
HB_MODES = {
    "disabled": HotBackupSetting.DISABLED,
    "directory": HotBackupSetting.DIRECTORY,
    "s3bucket": HotBackupSetting.S3BUCKET,
}


class InstallerFrontend:
    """class describing frontend instances"""

    def __init__(self, proto: str, ip_address: str, port: int):
        self.proto = proto
        self.ip_address = ip_address
        self.port = port


class InstallerConfig:
    """stores the baseline of this environment"""

    # pylint: disable=R0913 disable=R0902
    def __init__(
        self,
        version: str,
        verbose: bool,
        enterprise: bool,
        encryption_at_rest: bool,
        zip_package: bool,
        hot_backup: str,
        package_dir: Path,
        test_dir: Path,
        deployment_mode: str,
        publicip: str,
        interactive: bool,
        stress_upgrade: bool,
        ssl: bool,
    ):
        self.publicip = publicip
        self.interactive = interactive
        self.enterprise = enterprise
        self.encryption_at_rest = encryption_at_rest and enterprise
        self.zip_package = zip_package

        self.deployment_mode = deployment_mode
        self.verbose = verbose
        self.package_dir = package_dir
        self.have_system_service = True
        self.debug_package_is_installed = False
        self.client_package_is_installed = False
        self.server_package_is_installed = False
        self.stress_upgrade = stress_upgrade

        self.install_prefix = Path("/")

        self.base_test_dir = test_dir
        self.pwd = Path(os.path.dirname(os.path.realpath(__file__)))
        self.test_data_dir = self.pwd / ".." / ".." / ".." / "test_data"

        self.username = "root"
        self.passvoid = ""
        self.jwt = ""

        self.port = 8529
        self.localhost = "localhost"
        self.ssl = ssl

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
            self.enterprise and (semver.compare(self.version, "3.5.1") >= 0) and not isinstance(winver, list)
        )
        if self.hot_backup:
            self.hot_backup = hot_backup
        else:
            self.hot_backup = "disabled"
        self.hb_mode = HB_MODES[self.hot_backup]

    def __repr__(self):
        return """
version: {0.version}
using enterpise: {0.enterprise}
using encryption at rest: {0.encryption_at_rest}
using zip: {0.zip_package}
hot backup mode: {0.hot_backup}
package directory: {0.package_dir}
test directory: {0.base_test_dir}
deployment_mode: {0.deployment_mode}
public ip: {0.publicip}
interactive: {0.interactive}
verbose: {0.verbose}
""".format(
            self
        )

    def set_from(self, other_cfg):
        """copy constructor"""
        try:
            self.reset_version(other_cfg.version)
            self.publicip = other_cfg.publicip
            self.interactive = other_cfg.interactive
            self.enterprise = other_cfg.enterprise
            self.encryption_at_rest = other_cfg.encryption_at_rest
            self.zip_package = other_cfg.zip_package

            self.deployment_mode = other_cfg.deployment_mode
            self.verbose = other_cfg.verbose
            self.package_dir = other_cfg.package_dir
            self.have_system_service = other_cfg.have_system_service
            self.debug_package_is_installed = other_cfg.debug_package_is_installed
            self.client_package_is_installed = other_cfg.client_package_is_installed
            self.server_package_is_installed = other_cfg.server_package_is_installed
            self.stress_upgrade = other_cfg.stress_upgrade

            self.install_prefix = other_cfg.install_prefix

            self.base_test_dir = other_cfg.base_test_dir
            self.pwd = other_cfg.pwd
            self.test_data_dir = other_cfg.test_data_dir

            self.username = other_cfg.username
            self.passvoid = other_cfg.passvoid
            self.jwt = other_cfg.jwt

            self.port = other_cfg.port
            self.localhost = other_cfg.localhost
            self.ssl = other_cfg.ssl

            self.all_instances = other_cfg.all_instances
            self.frontends = other_cfg.frontends
            self.log_dir = other_cfg.log_dir
            self.bin_dir = other_cfg.bin_dir
            self.real_bin_dir = other_cfg.real_bin_dir
            self.sbin_dir = other_cfg.sbin_dir
            self.real_sbin_dir = other_cfg.real_sbin_dir
            self.dbdir = other_cfg.dbdir
            self.appdir = other_cfg.appdir
            self.cfgdir = other_cfg.cfgdir
            self.hot_backup = other_cfg.hot_backup
            self.hb_mode = other_cfg.hb_mode
        except AttributeError:
            # if the config.yml gave us a wrong value, we don't care.
            pass

    def reset_version(self, version):
        """establish a new version to manage"""
        self.version = version
        self.semver = semver.VersionInfo.parse(version)

    @step
    def add_frontend(self, proto, ip_address, port):
        """add a frontend URL in components"""
        self.frontends.append(InstallerFrontend(proto, ip_address, port))

    @step
    def set_frontend(self, proto, ip_address, port):
        """add a frontend URL in components"""
        self.frontends = [InstallerFrontend(proto, ip_address, port)]

    @step
    def generate_password(self):
        """generate a new password"""
        raise NotImplementedError()
        # self.passvoid = 'cde'

    @step
    def set_directories(self, other):
        """set all directories from the other object"""
        if other.base_test_dir is None:
            raise Exception("base_test_dir: must not copy in None!")
        self.base_test_dir = other.base_test_dir
        if other.bin_dir is None:
            raise Exception("bin_dir: must not copy in None!")
        self.bin_dir = other.bin_dir
        if other.sbin_dir is None:
            raise Exception("sbin_dir: must not copy in None!")
        self.sbin_dir = other.sbin_dir
        if other.real_bin_dir is None:
            raise Exception("real_bin_dir: must not copy in None!")
        self.real_bin_dir = other.real_bin_dir
        if other.real_sbin_dir is None:
            raise Exception("real_sbin_dir: must not copy in None!")
        self.real_sbin_dir = other.real_sbin_dir
        if other.log_dir is None:
            raise Exception("log_dir: must not copy in None!")
        self.log_dir = other.log_dir
        if other.dbdir is None:
            raise Exception("dbdir: must not copy in None!")
        self.dbdir = other.dbdir
        if other.appdir is None:
            raise Exception("appdir: must not copy in None!")
        self.appdir = other.appdir
        if other.cfgdir is None:
            raise Exception("cfgdir: must not copy in None!")
        self.cfgdir = other.cfgdir
        if other.install_prefix is None:
            raise Exception("install_prefix: must not copy in None!")
        self.install_prefix = other.install_prefix


# pylint: disable=import-outside-toplevel
def make_installer(install_config: InstallerConfig):
    # pylint: disable=too-many-return-statements
    """detect the OS and its distro,
    choose the proper installer
    and return it"""
    if install_config.zip_package:
        from arangodb.installers.tar import InstallerTAR

        return InstallerTAR(install_config)
    winver = platform.win32_ver()
    if winver[0]:
        from arangodb.installers.nsis import InstallerW

        return InstallerW(install_config)

    macver = platform.mac_ver()
    if macver[0]:
        from arangodb.installers.mac import InstallerMac

        return InstallerMac(install_config)

    if platform.system() in ["linux", "Linux"]:
        import distro

        distro = distro.linux_distribution(full_distribution_name=False)
        if distro[0] in ["debian", "ubuntu"]:
            from arangodb.installers.deb import InstallerDeb

            return InstallerDeb(install_config)
        if distro[0] in ["centos", "redhat", "suse", "rocky"]:
            from arangodb.installers.rpm import InstallerRPM

            return InstallerRPM(install_config)
        if distro[0] in ["alpine"]:
            from arangodb.installers.docker import InstallerDocker

            return InstallerDocker(install_config)
        raise Exception("unsupported linux distribution: " + str(distro))
    raise Exception("unsupported os" + platform.system())



class RunProperties:
    """bearer class for run properties"""
    # pylint: disable=too-many-function-args disable=too-many-arguments
    def __init__(self,
                 enterprise: bool,
                 encryption_at_rest: bool,
                 ssl: bool,
                 testrun_name: str = "",
                 directory_suffix: str = ""):
        """set the values for this testrun"""
        self.enterprise = enterprise
        self.encryption_at_rest = encryption_at_rest
        self.ssl = ssl
        self.testrun_name = testrun_name
        self.directory_suffix = directory_suffix

# pylint: disable=too-many-function-args
EXECUTION_PLAN = [
    RunProperties(True, True, True, "Enterprise\nEnc@REST", "EE"),
    RunProperties(True, False, False, "Enterprise", "EP"),
    RunProperties(False, False, False, "Community", "C"),
]

class InstallerBaseConfig:
    def __init__(self,
                 verbose: bool,
                 zip_package: bool,
                 hot_backup: str,
                 package_dir: Path,
                 test_data_dir: Path,
                 starter_mode: str,
                 publicip: str,
                 interactive: bool,
                 stress_upgrade: bool):
        self.verbose = verbose
        self.zip_package = zip_package
        self.hot_backup = hot_backup
        self.package_dir = package_dir
        self.test_data_dir = test_data_dir
        self.starter_mode = starter_mode
        self.publicip = publicip
        self.interactive = interactive
        self.stress_upgrade = stress_upgrade
    

# pylint: disable=too-many-locals
def create_config_installer_set(
    versions: list,
    base_config: InstallerBaseConfig,
    deployment_mode: str,
    run_properties: RunProperties
):
    """creates sets of configs and installers"""
    # pylint: disable=R0902 disable=R0913
    res = []
    for one_version in versions:
        print(str(one_version))
        install_config = InstallerConfig(
            str(one_version),
            base_config.verbose,
            run_properties.enterprise,
            run_properties.encryption_at_rest,
            base_config.zip_package,
            base_config.hot_backup,
            base_config.package_dir,
            base_config.test_data_dir,
            deployment_mode,
            base_config.publicip,
            base_config.interactive,
            base_config.stress_upgrade,
            run_properties.ssl,
        )
        installer = make_installer(install_config)
        res.append([install_config, installer])
    return res
