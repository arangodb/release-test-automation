#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys

import click
import semver

from common_options import very_common_options, common_options
from arangodb.installers import RunProperties
from arangodb.backup import HotBackupCliCfg
from test_driver import TestDriver


@click.command()
# pylint: disable=too-many-arguments disable=too-many-locals
@very_common_options()
@common_options(support_old=True, interactive=True)
# fmt: off
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, src_testing,
        hot_backup, hb_provider, hb_storage_path_prefix,
        hb_aws_access_key_id, hb_aws_secret_access_key, hb_aws_region, hb_aws_acl,
        # common_options
        old_version, test_data_dir, encryption_at_rest, interactive,
        starter_mode, stress_upgrade, abort_on_error, publicip,
        selenium, selenium_driver_args, alluredir, clean_alluredir,
        ssl, use_auto_certs):
    # fmt: on
    """ main trampoline """
    test_driver = TestDriver(
        verbose,
        Path(package_dir),
        Path(test_data_dir),
        Path(alluredir),
        clean_alluredir,
        zip_package,
        src_testing,
        HotBackupCliCfg(hot_backup,
                        hb_provider,
                        hb_storage_path_prefix,
                        hb_aws_access_key_id,
                        hb_aws_secret_access_key,
                        hb_aws_region,
                        hb_aws_acl),
        interactive,
        starter_mode,
        stress_upgrade,
        abort_on_error,
        publicip,
        selenium,
        selenium_driver_args,
        use_auto_certs)
    test_driver.set_r_limits()
    results = test_driver.run_upgrade(
        [
            semver.VersionInfo.parse(old_version),
            semver.VersionInfo.parse(new_version)
        ],
        RunProperties(enterprise,
                      encryption_at_rest,
                      ssl))
    print("V" * 80)
    status = True
    for one_result in results:
        print(one_result)
        status = status and one_result["success"]
    if not status:
        print("exiting with failure")
        sys.exit(1)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    main()
