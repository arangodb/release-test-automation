#!/usr/bin/python3
""" fetch nightly packages, process upgrade """
# pylint: disable=duplicate-code
import os
from pathlib import Path
import sys
import scp

import click
from common_options import very_common_options, download_options
from arangodb.installers import HotBackupCliCfg, InstallerBaseConfig
from download import (
    Download,
    DownloadOptions,
)

from tools.paramiko.server import RemoteClient
import tools.loghelper as lh

# fmt: off
@click.command()
@very_common_options()
@download_options()
@click.option('--push-hosts', 'push_hosts', type=click.STRING, multiple=True,   default=[])
@click.option('--push-user', 'push_user', type=click.STRING, default='tester')
@click.option('--ssh-key-file', 'ssh_key_file', type=click.STRING, default='~/.ssh/id_rsa.pub')
@click.option('--upload-path', 'upload_path', type=click.STRING, default='~/release-test-automation/package_cache')
def main(**kwargs):
    """ main """
    kwargs['interactive'] = False
    kwargs['abort_on_error'] = False
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path()
    kwargs['alluredir'] = Path()
    kwargs['starter_mode'] = 'all'
    kwargs['stress_upgrade'] = False
    kwargs['publicip'] = "127.0.0.1"

    kwargs['hb_mode'] = "disabled"
    kwargs['hb_provider'] = ""
    kwargs['hb_storage_path_prefix'] = ""
    kwargs['hb_cli_cfg'] = HotBackupCliCfg("disabled","","","","","","")

    kwargs['test'] = ''
    for one_host in kwargs['push_hosts']:
        try:
            (
                kwargs['push_host'],
                kwargs['force_arch'],
                kwargs['force_os']
            ) = one_host.split(':')
        except Exception as ex:
            print(f"--push-hosts syntax 'host:arch:os' have {one_host} - {ex}")
            sys.exit(1)

        kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)

        dl_opts = DownloadOptions.from_dict(**kwargs)
        lh.configure_logging(kwargs['verbose'])
        pw = ''
        if 'PASSVOID' in os.environ:
            pw=os.environ['PASSVOID']
        client = RemoteClient(kwargs['push_host'],
                              kwargs['push_user'],
                              pw,
                              kwargs['ssh_key_file'],
                              kwargs['upload_path'])
        client.execute_commands([
            'if test ! -d release-test-automation; then git clone https://github.com/arangodb/release-test-automation.git; else cd release-test-automation; git pull --all; fi',
            f'mkdir -p {kwargs["upload_path"]}'
        ])

        for zipit in [True, False]:
            for com_ep in [True, False]:
                downloader = Download(
                    options=dl_opts,
                    hb_cli_cfg=kwargs['hb_cli_cfg'],
                    version=kwargs['new_version'],
                    enterprise=com_ep,
                    zip_package=zipit,
                    src_testing=kwargs['src_testing'],
                    source=kwargs['source'],
                    force_arch=kwargs['force_arch'],
                    force_os=kwargs['force_os'])
                packages = downloader.get_packages(kwargs['force'])
                print(packages)
                try:
                    client.bulk_upload(packages)
                except scp.SCPException as ex:
                    print(f"FAILED to upload to {kwargs['push_host']}: {ex}")

    # client.disconnect()


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
