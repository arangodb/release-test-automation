#!/usr/bin/env python3
""" run an installer for the detected operating system """
import copy
import os
import platform
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import semver

from reporting.reporting_utils import step

try:
    # pylint: disable=no-name-in-module
    from tools.external_helpers import cloud_secrets
# pylint: disable=bare-except
except:
    # pylint: disable=invalid-name
    cloud_secrets = None

# pylint: disable=too-few-public-methods

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_MAC = platform.mac_ver()[0] != ""
DISTRO = ""


class HotBackupMode(Enum):
    """whether we want thot backup or not"""

    DISABLED = 0
    DIRECTORY = 1
    S3BUCKET = 2
    GCS = 3
    AZUREBLOBSTORAGE = 4


class HotBackupProviders(Enum):
    """list of cloud storage providers"""

    MINIO = 0
    AWS = 1
    GCE = 2
    AZURE = 3


hb_strings = {
    HotBackupMode.DISABLED: "disabled",
    HotBackupMode.DIRECTORY: "directory",
    HotBackupMode.S3BUCKET: "s3bucket",
    HotBackupMode.GCS: "googleCloudStorage",
    HotBackupMode.AZUREBLOBSTORAGE: "azureBlobStorage",
}
HB_MODES = {
    "disabled": HotBackupMode.DISABLED,
    "directory": HotBackupMode.DIRECTORY,
    "s3bucket": HotBackupMode.S3BUCKET,
    "googleCloudStorage": HotBackupMode.GCS,
    "azureBlobStorage": HotBackupMode.AZUREBLOBSTORAGE,
}

HB_PROVIDERS = {
    "minio": HotBackupProviders.MINIO,
    "aws": HotBackupProviders.AWS,
    "gce": HotBackupProviders.GCE,
    "azure": HotBackupProviders.AZURE,
}


class HotBackupProviderCfg:
    """different hotbackup upload setups"""

    ALLOWED_PROVIDERS = {
        HotBackupMode.DISABLED: [],
        HotBackupMode.DIRECTORY: [],
        HotBackupMode.S3BUCKET: [HotBackupProviders.MINIO, HotBackupProviders.AWS],
        HotBackupMode.GCS: [HotBackupProviders.GCE],
        HotBackupMode.AZUREBLOBSTORAGE: [HotBackupProviders.AZURE],
    }

    HB_PROVIDER_DEFAULT = {
        HotBackupMode.DISABLED: None,
        HotBackupMode.DIRECTORY: None,
        HotBackupMode.S3BUCKET: HotBackupProviders.MINIO,
        HotBackupMode.GCS: HotBackupProviders.GCE,
        HotBackupMode.AZUREBLOBSTORAGE: HotBackupProviders.AZURE,
    }

    def __init__(self, mode: str, provider: HotBackupProviders = None, path_prefix: str = None):
        self.mode = HB_MODES[mode]
        if provider and provider not in HotBackupProviderCfg.ALLOWED_PROVIDERS[self.mode]:
            raise Exception(f"Storage provider {provider} is not allowed for rclone config type {mode}!")
        if provider:
            self.provider = provider
        else:
            self.provider = HotBackupProviderCfg.HB_PROVIDER_DEFAULT[self.mode]
        self.path_prefix = path_prefix
        while self.path_prefix and "//" in self.path_prefix:
            self.path_prefix = self.path_prefix.replace("//", "/")


class OptionGroup:
    """wrapper class to init from kwargs"""

    @classmethod
    def from_dict(cls, **options):
        """invoke init from kwargs"""
        # these members will be added by derivative classes:
        # pylint: disable=no-member disable=fixme
        # TODO: after we upgrade to python 3.10, we should replace this with {}|{} operator
        dict1 = {key: value for key, value in options.items() if key in cls.__dataclass_fields__}
        dict2 = {
            key: value.type.from_dict(**options)
            for key, value in cls.__dataclass_fields__.items()
            if OptionGroup in value.type.mro()
        }
        for key, value in dict2.items():
            dict1[key] = value
        return cls(**(dict1))


@dataclass
class HotBackupCliCfg(OptionGroup):
    """map hotbackup_options"""

    # pylint: disable=too-many-instance-attributes disable=no-member disable=no-else-return disable=consider-iterating-dictionary
    @classmethod
    def from_dict(cls, **options):
        """invoke init from kwargs"""
        if "hb_use_cloud_preset" in options.keys() and options["hb_use_cloud_preset"] is not None:
            if hasattr(cloud_secrets, options["hb_use_cloud_preset"]):
                return cls(
                    **{
                        k: v
                        for k, v in getattr(cloud_secrets, options["hb_use_cloud_preset"]).items()
                        if k in cls.__dataclass_fields__
                    }
                )
            else:
                raise Exception("Presaved cloud profile with this name not found: " + options["hb_use_cloud_preset"])
        else:
            return cls(**{k: v for k, v in options.items() if k in cls.__dataclass_fields__})

    hb_mode: str
    hb_provider: str
    hb_storage_path_prefix: str

    # specific params for AWS
    hb_aws_access_key_id: str = None
    hb_aws_secret_access_key: str = None
    hb_aws_region: str = None
    hb_aws_acl: str = None

    # specific params for GCE
    hb_gce_service_account_credentials: str = None
    hb_gce_service_account_file: str = None
    hb_gce_project_number: str = None

    # specific params for Azure
    hb_azure_account: str = None
    hb_azure_key: str = None


class InstallerFrontend:
    """class describing frontend instances"""

    def __init__(self, proto: str, ip_address: str, port: int):
        self.proto = proto
        self.ip_address = ip_address
        self.port = port


class InstallerConfig:
    """stores the baseline of this environment"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-locals
    def __init__(
        self,
        version: str,
        verbose: bool,
        enterprise: bool,
        encryption_at_rest: bool,
        zip_package: bool,
        src_testing: bool,
        hb_cli_cfg: HotBackupCliCfg,
        package_dir: Path,
        test_dir: Path,
        deployment_mode: str,
        publicip: str,
        interactive: bool,
        stress_upgrade: bool,
        ssl: bool,
        one_shard: bool,
        use_auto_certs: bool,
        test: str,
        arangods: list,
        check_locale: bool,
    ):
        self.publicip = publicip
        self.interactive = interactive
        self.enterprise = enterprise
        self.encryption_at_rest = encryption_at_rest and enterprise
        self.zip_package = zip_package
        self.src_testing = src_testing

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
        self.test_data_dir = self.pwd / ".." / ".." / ".." / "rta-makedata" / "test_data"
        self.ui_data_dir = self.pwd / ".." / ".." / ".." / "test_data"

        self.username = "root"
        self.passvoid = ""
        self.jwt = ""

        self.port = 8529
        self.localhost = "localhost"
        self.ssl = ssl
        self.one_shard = one_shard
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
        self.hb_cli_cfg = hb_cli_cfg
        self.hb_provider_cfg = HotBackupProviderCfg(
            hb_cli_cfg.hb_mode,
            HB_PROVIDERS[hb_cli_cfg.hb_provider] if hb_cli_cfg.hb_provider else None,
            hb_cli_cfg.hb_storage_path_prefix,
        )
        self.hot_backup_supported = (
            self.enterprise and not IS_WINDOWS and self.hb_provider_cfg.mode != HotBackupMode.DISABLED
        )
        self.test = test
        self.arangods = arangods
        self.check_locale = check_locale

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
            self.enterprise = other_cfg.enterprise
            self.encryption_at_rest = other_cfg.encryption_at_rest
            self.zip_package = other_cfg.zip_package
            self.src_testing = other_cfg.src_testing

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
            self.check_locale = other_cfg.check_locale
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

    if platform.system() in ["linux", "Linux"]:
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
    def __init__(
        self,
        enterprise: bool,
        force_dl: bool = True,
        encryption_at_rest: bool = False,
        ssl: bool = False,
        replication2: bool = False,
        one_shard: bool = False,
        testrun_name: str = "",
        directory_suffix: str = "",
        minimum_supported_version: str = "3.5.0",
    ):
        """set the values for this testrun"""
        self.enterprise = enterprise
        self.force_dl = force_dl
        self.encryption_at_rest = encryption_at_rest
        self.ssl = ssl
        self.testrun_name = testrun_name
        self.directory_suffix = directory_suffix
        self.replication2 = replication2
        self.one_shard = one_shard
        self.minimum_supported_version = semver.VersionInfo.parse(minimum_supported_version)

    def __repr__(self):
        return """{0.__class__.__name__}
enterprise: {0.enterprise}
encryption_at_rest: {0.encryption_at_rest}
ssl: {0.ssl}
replication2: {0.replication2}
testrun_name: {0.testrun_name}
directory_suffix: {0.directory_suffix}""".format(
            self
        )


# pylint: disable=too-many-function-args
EXECUTION_PLAN = [
    RunProperties(True, True, True, True, False, False, "Enterprise\nEnc@REST", "EE"),
    RunProperties(True, True, True, True, False, True, "Enterprise\nOneShard", "OS"),
    # RunProperties(True, True, True, True, True, False, "Enterprise\nEnc@REST\nreplication v.2", "EEr2", "3.11.999"),
    RunProperties(True, False, False, False, False, False, "Enterprise", "EP"),
    # RunProperties(True, False, False, False, True, False, "Enterprise\nreplication v.2", "EPr2", "3.11.999"),
    RunProperties(False, True, False, False, False, False, "Community", "C"),
    # RunProperties(False, True, False, False, True, False, "Community\nreplication v.2", "Cr2", "3.11.999"),
]


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
    check_locale: bool


# pylint: disable=too-many-locals
def create_config_installer_set(
    versions: list,
    base_config: InstallerBaseConfig,
    deployment_mode: str,
    run_properties: RunProperties,
    use_auto_certs: bool,
):
    """creates sets of configs and installers"""
    # pylint: disable=too-many-instance-attributes disable=too-many-arguments
    res = []

    for one_version in versions:
        zipit = base_config.zip_package
        srcit = base_config.src_testing
        if str(one_version).find("src") >= 0:
            zipit = False
            srcit = True
        install_config = InstallerConfig(
            str(one_version),
            base_config.verbose,
            run_properties.enterprise,
            run_properties.encryption_at_rest,
            zipit,
            srcit,
            base_config.hb_cli_cfg,
            base_config.package_dir,
            base_config.test_data_dir,
            deployment_mode,
            base_config.publicip,
            base_config.interactive,
            base_config.stress_upgrade,
            run_properties.ssl,
            run_properties.one_shard,
            use_auto_certs,
            base_config.test,
            base_config.arangods,
            base_config.check_locale
        )
        installer = make_installer(install_config)
        installer.calculate_package_names()
        res.append([install_config, installer])
    return res
