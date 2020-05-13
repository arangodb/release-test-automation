#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path

import click
import sys

from tools.killall import kill_all_processes
from tools.quote_user import end_test
from arangodb.sh import ArangoshExecutor
import arangodb.installers as installers
from arangodb.starter.environment import get as getStarterenv
from arangodb.starter.environment import RunnerType
import tools.loghelper as lh

logging.basicConfig(
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)


@click.command()
@click.option('--old-version', help='old ArangoDB version number.')
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose',
              is_flag = True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--enterprise',
              is_flag = True,
              default=False,
              help='Enterprise or community?')
@click.option('--quote_user',
              default=True,
              help='wait for the user to hit Enter?')
@click.option('--starter-mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
def run_test(old_version, version, verbose, package_dir, enterprise, quote_user, starter_mode, publicip):
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("old version: " + str(old_version))
    print("using enterpise: " + str(enterprise))
    print("package directory: " + str(package_dir))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    #print("quote_user: " + str(no_quote_user))
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
            starter_mode.push(RunnerType.DC2DC)
    elif starter_mode == 'LF':
        starter_mode = [RunnerType.LEADER_FOLLOWER]
    elif starter_mode == 'AFO':
        starter_mode = [RunnerType.ACTIVE_FAILOVER]
    elif starter_mode == 'CL':
        starter_mode = [RunnerType.CLUSTER]
    elif starter_mode == 'DC':
        starter_mode = [RunnerType.DC2DC]
    elif starter_mode == 'none':
        starter_mode = [ None ]
    else:
        raise Exception("invalid starter mode: " + starter_mode)

    for runner in starter_mode:

        kill_all_processes()

        old_inst = installers.get(old_version,
                                  verbose,
                                  enterprise,
                                  Path(package_dir),
                                  publicip,
                                  quote_user)

        new_inst = installers.get(version,
                                  verbose,
                                  enterprise,
                                  Path(package_dir),
                                  publicip,
                                  quote_user)

        lh.section("install old: " + old_version)
        old_inst.install_package()

        if old_inst.check_service_up():
            old_inst.stop_service()

        if runner:
            stenv = getStarterenv(runner, old_inst.cfg)
            stenv.setup()
            stenv.run()
            stenv.post_setup()

        lh.section("install new: " + version)
        new_inst.upgrade_package()

        #check new version

        if new_inst.check_service_up():
            new_inst.stop_service()

        if runner:
            stenv.upgrade(new_inst.cfg)
            # end_test(inst.cfg, runner)
            stenv.shutdown()
            stenv.cleanup()
            kill_all_processes()
        else:
            new_inst.start_service()
            new_inst.check_service_up()

            pwcheckarangosh = ArangoshExecutor(new_inst.cfg)
            if not pwcheckarangosh.js_version_check():
                logging.error(
                    "Version Check failed -"
                    "probably setting the default random password didn't work! %s",
                    new_inst.cfg.passvoid)
                sys.exit(1)

        lh.section("uninstall")
        new_inst.un_install_package()
        lh.section("check system")
        new_inst.check_uninstall_cleanup()
        lh.section("remove residuals")
        new_inst.cleanup_system()


if __name__ == "__main__":
    run_test()
