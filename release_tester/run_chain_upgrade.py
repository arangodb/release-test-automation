#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
import platform
import sys

# pylint: disable=duplicate-code
from pathlib import Path

import click

from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig
from common_options import very_common_options, common_options, download_options, full_common_options, \
    hotbackup_options, ui_test_suite_filtering_options
from download import DownloadOptions
from full_download_upgrade_test import upgrade_package_test
from test_driver import TestDriver
from tools.release_tracker_client.client import ReleaseTrackerApiClient, OS, Arch


@click.command()
@full_common_options
@click.option(
    "--release-tracker-hostname", default="release-tracker.arangodb.com", help="hostname of the release tracker API"
)
@click.option("--release-tracker-port", default="443", help="port number of the release tracker API")
@click.option(
    "--release-tracker-protocol", default="https", help="protocol of the release tracker API(e.g. http or https)"
)
@click.option("--release-tracker-username", default="", help="username for the release tracker API")
@click.option("--release-tracker-password", default="", help="password for the release tracker API")
@very_common_options()
@hotbackup_options()
@common_options(
    support_multi_version=False,
    support_old=False,
    interactive=False,
    test_data_dir="/home/test_dir",
)
@download_options(default_source="nightlypublic", other_source=True)
@ui_test_suite_filtering_options()
# fmt: off
# pylint: disable=too-many-arguments, disable=unused-argument, disable=invalid-name
def main(**kwargs):
    """ main """
    kwargs['interactive'] = False
    kwargs['abort_on_error'] = False
    kwargs['stress_upgrade'] = False
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path(kwargs['test_data_dir'])
    kwargs['alluredir'] = Path(kwargs['alluredir'])

    kwargs['hb_cli_cfg'] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)
    dl_opts = DownloadOptions.from_dict(**kwargs)

    os = None
    if platform.win32_ver()[0] != "":
        os = OS.WINDOWS
    elif platform.mac_ver()[0] != "":
        os = OS.MACOS
    elif platform.system() in ["linux", "Linux"]:
        os = OS.LINUX
    else:
        raise Exception("Unable to detect OS.")
    cpu_arch = None
    if platform.uname().machine.lower() in ["x86_64", "amd64"]:
        cpu_arch = Arch.X86
    else:
        cpu_arch = Arch.ARM
    release_tracker_client = ReleaseTrackerApiClient(host=kwargs['release_tracker_hostname'],
                                                     port=kwargs['release_tracker_port'],
                                                     protocol=kwargs['release_tracker_protocol'],
                                                     username=kwargs['release_tracker_username'],
                                                     password=kwargs['release_tracker_password'])
    nightly_branches = release_tracker_client.nightly_branches()
    oldest_branch = nightly_branches[0]
    devel_branch = nightly_branches[-1]
    upgrade_list = []
    upgrade_list.append(release_tracker_client.get_latest_release_if_any(oldest_branch, os, cpu_arch))
    upgrade_list.append(release_tracker_client.get_latest_nightly_if_any(oldest_branch, os, cpu_arch))
    for branch in nightly_branches[1:-1]:
        upgrade_list.append(release_tracker_client.get_latest_release_if_any(branch, os, cpu_arch))
        upgrade_list.append(release_tracker_client.get_latest_nightly_if_any(branch, os, cpu_arch))
    upgrade_list.append(release_tracker_client.get_latest_release_if_any(devel_branch, os, cpu_arch))
    upgrade_list.append(release_tracker_client.get_latest_nightly_if_any(devel_branch, os, cpu_arch))
    while None in upgrade_list:
        upgrade_list.remove(None)
    upgrade_matrix = ":".join(upgrade_list)

    test_driver = TestDriver(**kwargs)
    try:
        results = upgrade_package_test(
            dl_opts,
            new_version,
            kwargs['source'],
            upgrade_matrix,
            kwargs['other_source'],
            kwargs['git_version'],
            kwargs['editions'],
            False,
            False,
            test_driver
        )
    finally:
        test_driver.destructor()
    return results


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
