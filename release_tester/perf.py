#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import re
import click
from common_options import very_common_options, common_options
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments.cluster_perf import ClusterPerf
from arangodb.starter.deployments import RunnerType
import tools.loghelper as lh

@click.command()
@click.option('--mode',
              type=click.Choice(["all", "install", "uninstall", "tests", ]),
              default='all',
              help='operation mode.')

@click.option('--scenario',
              default='scenarios/cluster_replicated.yml',
              help='test configuration yaml file, default written & exit if not there.')
@click.option('--frontends',
              multiple=True,
              help='Connection strings of remote clusters')
@very_common_options
@common_options(support_old=False)
# pylint: disable=R0913 disable=W0613
def run_test(mode, scenario, frontends,
             #very_common_options
             new_version,
             verbose,
             enterprise,
             package_dir,
             zip_package,
             # common_options
             # old_version,
             test_data_dir,
             encryption_at_rest,
             interactive,
             starter_mode,
             stress_upgrade,
             abort_on_error,
             publicip,
             selenium,
             selenium_driver_args):
    """ main """
    lh.configure_logging(verbose)

    lh.section("configuration")
    print("version: " + str(new_version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip_package))
    print("package directory: " + str(package_dir))
    print("mode: " + str(mode))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("scenario: " + str(scenario))
    print("verbose: " + str(verbose))

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    lh.section("startup")

    install_config = InstallerConfig(new_version,
                                     verbose,
                                     enterprise,
                                     encryption_at_rest,
                                     zip_package,
                                     Path(package_dir),
                                     Path(test_data_dir),
                                     mode,
                                     publicip,
                                     interactive,
                                     False)

    split_host = re.compile(r'([a-z]*)://([0-9.:]*):(\d*)')

    inst = make_installer(install_config)

    if len(frontends) > 0:
        for frontend in frontends:
            print('remote')
            host_parts = re.split(split_host, frontend)
            inst.cfg.add_frontend(host_parts[1],
                                  host_parts[2],
                                  host_parts[3])
    inst.cfg.scenario = Path(scenario)
    runner = ClusterPerf(RunnerType.CLUSTER,
                         inst.cfg, inst,
                         None, None,
                         selenium,
                         selenium_driver_args,
                         "perf")
    runner.do_install = do_install
    runner.do_uninstall = do_uninstall
    failed = False
    if not runner.run():
        failed = True

    if len(frontends) == 0:
        kill_all_processes()

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(run_test())
