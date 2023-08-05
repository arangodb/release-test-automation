#!/usr/bin/env python3
""" Release testing script"""
# pylint: disable=duplicate-code

from pathlib import Path
import click
import tools.loghelper as lh
from arangodb.installers import RunProperties, HotBackupCliCfg, InstallerBaseConfig
from arangodb.installers.base import InstallerBase
from common_options import zip_common_options
from test_driver import TestDriver


@click.command()
@zip_common_options
def main(**kwargs):
    """Wrapper..."""
    lh.configure_logging(True)

    kwargs["verbose"] = False
    kwargs["package_dir"] = Path("")
    kwargs["test_data_dir"] = Path("")
    kwargs["alluredir"] = Path("")
    kwargs["clean_alluredir"] = True
    kwargs["hb_mode"] = "disabled"
    kwargs["hb_provider"] = ""
    kwargs["hb_storage_path_prefix"] = ""
    kwargs["hb_aws_access_key_id"] = ""
    kwargs["hb_aws_secret_access_key"] = ""
    kwargs["hb_aws_region"] = ""
    kwargs["hb_aws_acl"] = ""
    kwargs["hb_gce_service_account_credentials"] = ""
    kwargs["hb_gce_service_account_file"] = ""
    kwargs["hb_gce_project_number"] = ""
    kwargs["hb_azure_key"] = ""
    kwargs["hb_azure_account"] = ""
    kwargs["interactive"] = False
    kwargs["starter_mode"] = "all"
    kwargs["stress_upgrade"] = False
    kwargs["abort_on_error"] = False
    kwargs["publicip"] = "127.0.0.1"
    kwargs["selenium"] = "none"
    kwargs["selenium_driver_args"] = []
    kwargs["use_auto_certs"] = False
    kwargs["test"] = ""
    kwargs["monitoring"] = False

    # pylint: disable=broad-except disable=bare-except
    versions = ["3.3.3"]
    enterprise = False
    try:
        saved_cfg = InstallerBase.load_config_from_file()
        kwargs["zip_package"] = saved_cfg.zip_package
        kwargs["src_testing"] = saved_cfg.src_testing
        kwargs["package_dir"] = saved_cfg.package_dir
        versions = [saved_cfg.version]
        enterprise = saved_cfg.enterprise
    except:
        print("Failed to load parameters from pre-saved configuration file.")

    kwargs["hb_cli_cfg"] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs["base_config"] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)
    try:
        test_driver.set_r_limits()
        test_driver.run_cleanup(RunProperties(enterprise, False, False), versions)
    finally:
        test_driver.destructor()


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
