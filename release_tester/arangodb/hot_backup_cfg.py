#!/usr/bin/env python3
""" run an installer for the detected operating system """

from dataclasses import dataclass
from enum import Enum

from tools.option_group import OptionGroup

try:
    # pylint: disable=no-name-in-module
    from tools.external_helpers import cloud_secrets
# pylint: disable=bare-except
except:
    # pylint: disable=invalid-name
    cloud_secrets = None

class HotBackupMode(Enum):
    """whether we want thot backup or not"""

    DISABLED = 0
    DIRECTORY = 1
    S3BUCKET = 2
    GCS = 3
    AZUREBLOBSTORAGE = 4

# pylint: disable=too-few-public-methods
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
