#!/usr/bin/env python3
""" Release testing script"""
#pylint: disable=duplicate-code

from pathlib import Path
import os
import sys
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig,  HotBackupCliCfg, InstallerBaseConfig
from arangodb.starter.deployments.testing import Testing
from arangodb.starter.deployments import RunnerType
import tools.loghelper as lh
from reporting.reporting_utils import init_allure

from common_options import very_common_options, common_options

@click.command()
@click.option(
    "--mode",
    type=click.Choice(
        [
            "all",
            "install",
            "uninstall",
            "tests",
        ]
    ),
    default="all",
    help="operation mode.",
)
@click.option('--scenario',
              default='scenarios/testing.js/',
              help='test configuration yaml file, default written & exit if not there.')
@click.option("--frontends", multiple=True, help="Connection strings of remote clusters")
@very_common_options
@common_options(support_old=False)
def main(**kwargs):
    """ main """
    kwargs['stress_upgrade'] = False
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path(kwargs['test_data_dir'])
    kwargs['alluredir'] = Path(kwargs['alluredir'])

    kwargs['hb_cli_cfg'] = HotBackupCliCfg("disabled","","","","","","")
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)

    do_install = kwargs['mode'] in ["all", "install"]
    do_uninstall = kwargs['mode'] in ["all", "uninstall"]

    launch_dir = Path.cwd()
    if "WORKSPACE" in os.environ:
        launch_dir = Path(os.environ["WORKSPACE"])

    if not kwargs['test_data_dir'].is_absolute():
        kwargs['test_data_dir'] = launch_dir / kwargs['test_data_dir']
    if not kwargs['test_data_dir'].exists():
        kwargs['test_data_dir'].mkdir(parents=True, exist_ok=True)
    os.chdir(kwargs['test_data_dir'])

    if not kwargs['package_dir'].is_absolute():
        kwargs['package_dir'] = (launch_dir / kwargs['package_dir']).resolve()
    if not kwargs['package_dir'].exists():
        kwargs['package_dir'].mkdir(parents=True, exist_ok=True)

    init_allure(results_dir=kwargs['alluredir'],
                clean=kwargs['clean_alluredir'],
                zip_package=kwargs['zip_package'])


    lh.section("startup")

    install_config = InstallerConfig(kwargs['new_version'],
                                     kwargs['verbose'],
                                     kwargs['enterprise'],
                                     kwargs['encryption_at_rest'],
                                     kwargs['zip_package'],
                                     kwargs['src_testing'],
                                     kwargs['hb_cli_cfg'],
                                     kwargs['package_dir'],
                                     kwargs['test_data_dir'],
                                     kwargs['mode'],
                                     kwargs['publicip'],
                                     kwargs['interactive'],
                                     False, False)
    install_config.source = True

    inst = make_installer(install_config)

    inst.cfg.scenario = Path(kwargs['scenario'])
    runner = Testing(RunnerType.TESTING,
                     False,
                     inst,
                     kwargs['selenium'],
                     kwargs['selenium_driver_args'],
                     "bla",
                     False,
                     False)
    runner.do_install = do_install
    runner.do_uninstall = do_uninstall
    failed = False
    if not runner.starter_prepare_env_impl():
        failed = True

    if len(kwargs['frontends']) == 0:
        kill_all_processes()

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
