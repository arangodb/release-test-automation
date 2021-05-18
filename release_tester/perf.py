#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import re
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments.cluster_perf import ClusterPerf
from arangodb.starter.deployments import RunnerType
import tools.loghelper as lh

@click.command()
@click.option('--old-version', help='unused')
@click.option('--new-version', help='ArangoDB version number.')
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--encryption-at-rest/--no-encryption-at-rest',
              is_flag=True,
              default=False,
              help='turn on encryption at rest for Enterprise packages')
@click.option('--zip/--no-zip', 'zip_package',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=False,
              help='wait for the user to hit Enter?')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--test-data-dir',
              default='/tmp/',
              help='directory create databases etc. in.')
@click.option('--mode',
              default='all',
              help='operation mode - [all|install|uninstall|tests].')
@click.option('--starter-mode',
              default='all',
              help='which starter deployments modes to use - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')

@click.option('--scenario',
              default='scenarios/cluster_replicated.yml',
              help='test configuration yaml file, default written & exit if not there.')
@click.option('--frontends',
              multiple=True,
              help='Connection strings of remote clusters')
@click.option('--selenium',
              default='none',
              help='if non-interactive chose the selenium target')
@click.option('--selenium-driver-args',
              default=[],
              multiple=True,
              help='options to the selenium web driver')
# pylint: disable=R0913
def run_test(old_version, new_version, verbose, package_dir, test_data_dir,
             enterprise, encryption_at_rest, zip_package,
             interactive, mode, starter_mode, publicip, scenario, frontends,
             selenium, selenium_driver_args):
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

    if mode not in ['all', 'install', 'system', 'tests', 'uninstall']:
        raise Exception("unsupported mode %s!" % mode)

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
    runner = ClusterPerf(RunnerType.CLUSTER, inst.cfg, inst, None, None, selenium, selenium_driver_args, "perf")
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
