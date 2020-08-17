#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path

import sys
import click

from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner
import tools.loghelper as lh

logging.basicConfig(
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)


@click.command()
@click.option('--old-version', help='old ArangoDB version number.')
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--zip/--no-zip',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
              help='wait for the user to hit Enter?')
@click.option('--starter-mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
def run_test(old_version, version, verbose, package_dir,
             enterprise, zip, interactive, starter_mode, publicip):
    """ main """
    lh.section("configuration")
    print("old version: " + str(old_version))
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip))
    print("package directory: " + str(package_dir))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    if starter_mode == 'all':
        starter_mode = [RunnerType.LEADER_FOLLOWER,
                        RunnerType.ACTIVE_FAILOVER,
                        RunnerType.CLUSTER]
        if enterprise:
            starter_mode.append(RunnerType.DC2DC)
    elif starter_mode == 'LF':
        starter_mode = [RunnerType.LEADER_FOLLOWER]
    elif starter_mode == 'AFO':
        starter_mode = [RunnerType.ACTIVE_FAILOVER]
    elif starter_mode == 'CL':
        starter_mode = [RunnerType.CLUSTER]
    elif starter_mode == 'DC':
        starter_mode = [RunnerType.DC2DC]
    elif starter_mode == 'none':
        starter_mode = [None]
    else:
        raise Exception("invalid starter mode: " + starter_mode)

    for runner_type in starter_mode:

        kill_all_processes()
        install_config_old = InstallerConfig(old_version,
                                             verbose,
                                             enterprise, 
                                             zip, 
                                             Path(package_dir),
                                             'all',
                                             publicip,
                                             interactive)
        old_inst = make_installer(install_config_old)
        install_config_new = InstallerConfig(version,
                                             verbose,
                                             enterprise,
                                             zip,
                                             Path(package_dir),
                                             'all',
                                             publicip,
                                             interactive)
        new_inst = make_installer(install_config_new)

        runner = None
        if runner_type:
            runner = make_runner(runner_type,
                                 install_config_old,
                                 old_inst,
                                 install_config_new,
                                 new_inst)

            if runner:
                runner.run()

        lh.section("uninstall")
        new_inst.un_install_package()
        lh.section("check system")
        new_inst.check_uninstall_cleanup()
        lh.section("remove residuals")
        new_inst.cleanup_system()


if __name__ == "__main__":
    run_test()
