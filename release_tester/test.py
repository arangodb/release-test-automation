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
    level=logging.INFO,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)


@click.command()
@click.option('--old-version', help='unused')
@click.option('--new-version', help='ArangoDB version number.', default="3.8.0-nightly")
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--zip/--no-zip', "zip_package",
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
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
              '[all|LF|AFO|CL|DC|DCEndurance|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
# pylint: disable=R0913 disable=R0914
def run_test(old_version, new_version, verbose,
             package_dir, test_data_dir,
             enterprise, zip_package,
             interactive, mode, starter_mode, publicip):
    """ main """
    lh.section("configuration")
    print("version: " + str(new_version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip_package))
    print("package directory: " + str(package_dir))
    print("mode: " + str(mode))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    if mode not in ['all', 'install', 'system', 'tests', 'uninstall']:
        raise Exception("unsupported mode %s!" % mode)

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    install_config = InstallerConfig(new_version,
                                     verbose,
                                     enterprise,
                                     zip_package,
                                     Path(package_dir),
                                     Path(test_data_dir),
                                     mode,
                                     publicip,
                                     interactive,
                                     False)

    inst = make_installer(install_config)

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
    elif starter_mode == 'DCendurance':
        starter_mode = [RunnerType.DC2DCENDURANCE]
    elif starter_mode == 'none':
        starter_mode = [RunnerType.NONE]
    else:
        raise Exception("invalid starter mode: " + starter_mode)

    count = 1
    for runner_type in starter_mode:
        assert runner_type
        runner = make_runner(runner_type, inst.cfg, inst, None)
        # install on first run:
        runner.do_install = (count == 1) and do_install
        # only uninstall after the last test:
        runner.do_uninstall = (count == len(starter_mode)) and do_uninstall
        failed = False
        if not runner.run():
            failed = True

        kill_all_processes()
        count += 1

    return 0 if not failed else 1


if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    sys.exit(run_test())
