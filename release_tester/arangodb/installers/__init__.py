#!/usr/bin/env python3
""" run an installer for the detected operating system """
import copy
import os
import platform
from dataclasses import dataclass
from pathlib import Path

import semver

from tools.option_group import OptionGroup

from reporting.reporting_utils import step

from arangodb.hot_backup_cfg import HotBackupCliCfg, HotBackupProviderCfg, HotBackupMode, HB_PROVIDERS

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_MAC = platform.mac_ver()[0] != ""
SYSTEM = platform.system()
DISTRO = ""


@dataclass
class InstallerBaseConfig(OptionGroup):
    """commandline argument config settings"""

    # pylint: disable=too-many-instance-attributes
    verbose: bool
    zip_package: bool
    src_testing: bool
    hb_cli_cfg: HotBackupCliCfg
    package_dir: Path
    test_data_dir: Path
    starter_mode: str
    publicip: str
    interactive: bool
    stress_upgrade: bool
    test: str
    skip: str
    check_locale: bool
    checkdata: bool
    is_instrumented: bool


class InstallerFrontend:
    # pylint: disable=too-few-public-methods
    """class describing frontend instances"""

    def __init__(self, proto: str, ip_address: str, port: int):
        self.proto = proto
        self.ip_address = ip_address
        self.port = port


class InstallerConfig:
    """stores the baseline of this environment"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    # pylint: disable=too-many-locals disable=too-many-statements disable=invalid-name
    def __init__(
        self,
        version: str,
        enterprise: bool,
        encryption_at_rest: bool,
        bc: InstallerBaseConfig,
        deployment_mode: str,
        ssl: bool,
        force_one_shard: bool,
        use_auto_certs: bool,
        arangods: list,
        mixed: bool,
    ):
        self.publicip = bc.publicip
        self.interactive = bc.interactive
        self.is_instrumented = bc.is_instrumented
        self.enterprise = enterprise
        self.encryption_at_rest = encryption_at_rest and enterprise
        self.zip_package = bc.zip_package
        self.src_testing = bc.src_testing

        self.supports_rolling_upgrade = not IS_WINDOWS
        self.verbose = bc.verbose
        self.package_dir = bc.package_dir
        self.have_system_service = not self.zip_package and self.src_testing
        self.debug_package_is_installed = False
        self.client_package_is_installed = False
        self.server_package_is_installed = False
        self.stress_upgrade = bc.stress_upgrade

        self.deployment_mode = deployment_mode

        self.install_prefix = Path("/")

        self.base_test_dir = bc.test_data_dir
        self.pwd = Path(os.path.dirname(os.path.realpath(__file__)))
        self.test_data_dir = self.pwd / ".." / ".." / ".." / "rta-makedata" / "test_data"
        self.ui_data_dir = self.pwd / ".." / ".." / ".." / "test_data"
        self.sublaunch_pwd = self.test_data_dir

        self.username = "root"
        self.passvoid = ""
        self.jwt = ""

        self.port = 8529
        self.localhost = "localhost"
        self.ssl = ssl
        self.force_one_shard = force_one_shard
        self.use_auto_certs = use_auto_certs

        self.all_instances = {}
        self.frontends = []
        self.default_arangosh_args = []
        self.default_starter_args = []
        self.default_backup_args = []
        self.default_imp_args = []
        self.default_restore_args = []

        self.reset_version(version)
        self.log_dir = Path()
        self.bin_dir = Path()
        self.real_bin_dir = Path()
        self.sbin_dir = Path()
        self.real_sbin_dir = Path()
        self.dbdir = Path()
        self.appdir = Path()
        self.cfgdir = Path()
        self.hb_cli_cfg = bc.hb_cli_cfg
        self.hb_provider_cfg = HotBackupProviderCfg(
            bc.hb_cli_cfg.hb_mode,
            HB_PROVIDERS[bc.hb_cli_cfg.hb_provider] if bc.hb_cli_cfg.hb_provider else None,
            bc.hb_cli_cfg.hb_storage_path_prefix,
        )
        self.hot_backup_supported = (
            self.enterprise and not IS_WINDOWS and self.hb_provider_cfg.mode != HotBackupMode.DISABLED
        )
        self.test = bc.test
        self.skip = bc.skip
        self.arangods = arangods
        self.check_locale = bc.check_locale
        self.checkdata = bc.checkdata
        self.mixed = mixed

    def __repr__(self):
        return """
version: {0.version}
using enterpise: {0.enterprise}
using encryption at rest: {0.encryption_at_rest}
using zip: {0.zip_package}
using source: {0.src_testing}
using binary dir: {0.real_bin_dir}
hot backup mode: {0.hot_backup_supported}
package directory: {0.package_dir}
test directory: {0.base_test_dir}
deployment_mode: {0.deployment_mode}
public ip: {0.publicip}
interactive: {0.interactive}
verbose: {0.verbose}
test filter: {0.test}
skip filter: {0.skip}
run make/check data: {0.checkdata}
sublaunch pwd = {0.sublaunch_pwd}
""".format(
            self
        )

    # pylint: disable=attribute-defined-outside-init
    def set_from(self, other_cfg):
        """copy constructor"""
        try:
            self.reset_version(other_cfg.version)
            self.default_arangosh_args = copy.deepcopy(other_cfg.default_arangosh_args)
            self.default_starter_args = copy.deepcopy(other_cfg.default_starter_args)
            self.default_backup_args = copy.deepcopy(other_cfg.default_backup_args)
            self.default_imp_args = copy.deepcopy(other_cfg.default_imp_args)
            self.default_restore_args = copy.deepcopy(other_cfg.default_restore_args)
            self.publicip = other_cfg.publicip
            self.interactive = other_cfg.interactive
            self.is_instrumented = other_cfg.is_instrumented
            self.enterprise = other_cfg.enterprise
            self.encryption_at_rest = other_cfg.encryption_at_rest
            self.zip_package = other_cfg.zip_package
            self.src_testing = other_cfg.src_testing

            self.deployment_mode = other_cfg.deployment_mode
            self.supports_rolling_upgrade = other_cfg.supports_rolling_upgrade
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
            self.sublaunch_pwd = other_cfg.sublaunch_pwd

            self.username = other_cfg.username
            self.passvoid = other_cfg.passvoid
            self.jwt = other_cfg.jwt

            self.port = other_cfg.port
            self.localhost = other_cfg.localhost
            self.ssl = other_cfg.ssl
            self.version = other_cfg.version

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
            self.hot_backup_supported = other_cfg.hot_backup_supported
            self.hb_cli_cfg = copy.deepcopy(other_cfg.hb_cli_cfg)
            self.test = other_cfg.test
            self.skip = other_cfg.skip
            self.check_locale = other_cfg.check_locale
            self.checkdata = other_cfg.checkdata
            self.mixed = other_cfg.mixed
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

    # pylint: disable=too-many-branches
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
        if other.version is None:
            raise Exception("version: must not copy in None!")
        self.version = other.version
        if other.semver is None:
            raise Exception("semver: must not copy in None!")
        self.semver = other.semver
        if self.zip_package:
            if other.client_install_prefix is None:
                raise Exception("client_install_prefix: must not copy in None!")
            self.client_install_prefix = other.client_install_prefix
            if other.server_install_prefix is None:
                raise Exception("server_install_prefix: must not copy in None!")
            self.server_install_prefix = other.server_install_prefix


# pylint: disable=import-outside-toplevel
def make_installer(install_config: InstallerConfig):
    # pylint: disable=too-many-return-statements
    """detect the OS and its distro,
    choose the proper installer
    and return it"""
    if install_config.src_testing:
        from arangodb.installers.source import InstallerSource

        return InstallerSource(install_config)

    if IS_WINDOWS:
        if install_config.zip_package:
            from arangodb.installers.zip import InstallerZip

            return InstallerZip(install_config)

        from arangodb.installers.nsis import InstallerNsis

        return InstallerNsis(install_config)

    if install_config.zip_package:
        from arangodb.installers.tar import InstallerTAR

        return InstallerTAR(install_config)

    if IS_MAC:
        from arangodb.installers.mac import InstallerMac

        return InstallerMac(install_config)

    if SYSTEM in ["linux", "Linux"]:
        dist = DISTRO
        import distro

        if DISTRO == "":
            dist = distro.linux_distribution(full_distribution_name=False)[0]
        if dist in ["debian", "ubuntu"]:
            from arangodb.installers.deb import InstallerDeb

            return InstallerDeb(install_config)
        if dist in ["centos", "redhat", "suse", "rocky"]:
            from arangodb.installers.rpm import InstallerRPM

            return InstallerRPM(install_config)
        if dist in ["alpine"]:
            from arangodb.installers.docker import InstallerDocker

            return InstallerDocker(install_config)
        raise Exception("unsupported linux distribution: " + str(distro))
    raise Exception("unsupported os" + platform.system())


class RunProperties:
    """bearer class for run properties"""

    # pylint: disable=too-many-function-args disable=too-many-arguments disable=too-many-instance-attributes
    # pylint: disable=too-many-locals
    def __init__(
        self,
        enterprise: bool,
        mixed: bool = False,
        force_dl: bool = True,
        encryption_at_rest: bool = False,
        ssl: bool = False,
        replication2: bool = False,
        force_one_shard: bool = False,
        create_oneshard_db: bool = False,
        testrun_name: str = "",
        directory_suffix: str = "",
        only_zip_src: bool = False,
        minimum_supported_version: str = "3.5.0",
        maximum_supported_version: str = "10.0.0",
        use_auto_certs: bool = False,
        cluster_nodes: int = 3,
    ):
        """set the values for this testrun"""
        if (create_oneshard_db or force_one_shard) and not enterprise:
            raise Exception("--create-oneshard-db and --force-oneshard options are not supported in Community edition")
        self.enterprise = enterprise
        self.mixed = mixed
        self.force_dl = force_dl
        self.encryption_at_rest = encryption_at_rest
        self.use_auto_certs = use_auto_certs
        self.ssl = ssl
        self.testrun_name = testrun_name
        self.directory_suffix = directory_suffix
        self.replication2 = replication2
        self.force_one_shard = force_one_shard
        self.create_oneshard_db = create_oneshard_db
        self.minimum_supported_version = semver.VersionInfo.parse(minimum_supported_version)
        self.maximum_supported_version = semver.VersionInfo.parse(maximum_supported_version)
        self.cluster_nodes = cluster_nodes
        self.only_zip_src = only_zip_src

    def is_version_not_supported(self, version):
        """ check whether this edition is supported in version """
        ver = semver.VersionInfo.parse(version)
        return not (self.maximum_supported_version > ver > self.minimum_supported_version)

    def set_kwargs(self, kwargs):
        """pick values from the commandline arguments that should override defaults"""
        self.use_auto_certs = kwargs["use_auto_certs"]
        self.cluster_nodes = kwargs["cluster_nodes"]

    def __repr__(self):
        return """Runner Scenario => {0.directory_suffix}
  enterprise: {0.enterprise}
  encryption_at_rest: {0.encryption_at_rest}
  ssl: {0.ssl}
  replication2: {0.replication2}
  testrun_name: {0.testrun_name}""".format(
            self
        )


# pylint: disable=too-many-function-args disable=line-too-long
EXECUTION_PLAN = [
    RunProperties(False, False, True, False, False, False, False, False, "Community", "C", False, "3.5.0", "3.12.4"),
    RunProperties(False, True, True, False, False, False, False, False, "CommunityEnterprise", "CE", True, "3.5.0", "3.12.4"),
    RunProperties(True, False, True, True, True, False, False, True, "Enterprise\nEnc@REST", "EE"),
    RunProperties(True, False, True, True, True, False, True, False, "Enterprise\nforced OneShard", "OS"),
    # RunProperties(True, False, True, True, True, True, False, True, "Enterprise\nEnc@REST\nreplication v.2", "EEr2", False, "3.11.999"),
    RunProperties(True, False, False, False, False, False, False, True, "Enterprise", "EP"),
    # RunProperties(True, False, False, False, False, True, False, True, "Enterprise\nreplication v.2", "EPr2", False, "3.11.999"),
]


# pylint: disable=too-many-locals
def create_config_installer_set(
    versions: list,
    base_config: InstallerBaseConfig,
    deployment_mode: str,
    run_properties: RunProperties,
):
    """creates sets of configs and installers"""
    # pylint: disable=too-many-instance-attributes disable=too-many-arguments
    res = []

    ep = run_properties.enterprise
    for one_version in versions:
        one_cfg = copy.deepcopy(base_config)
        if str(one_version).find("src") >= 0:
            one_cfg.zip_package = False
            one_cfg.src_testing = True
        install_config = InstallerConfig(
            str(one_version),
            ep,
            run_properties.encryption_at_rest,
            one_cfg,
            deployment_mode,
            run_properties.ssl,
            run_properties.force_one_shard,
            run_properties.use_auto_certs,
            base_config.arangods,
            run_properties.mixed,
        )
        installer = make_installer(install_config)
        installer.calculate_package_names()
        res.append([install_config, installer])
        if run_properties.mixed:
            ep = True
    return res
