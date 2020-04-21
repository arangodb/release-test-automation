#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path

import click

from tools.killall import kill_all_processes
from tools.quote_user import end_test
from arangodb.sh import ArangoshExecutor
import arangodb.installers as installers
from arangodb.starter.environment import get as getStarterenv
from arangodb.starter.environment import RunnerType

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


@click.command()
@click.option('--old_version', help='old ArangoDB version number.')
@click.option('--version', help='ArangoDB version number.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--enterprise',
              default='True',
              help='Enterprise or community?')
@click.option('--quote_user',
              default='True',
              help='wait for the user to hit Enter?')
@click.option('--starter_mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
def run_test(old_version, version, package_dir, enterprise, quote_user, starter_mode, publicip):
    """ main """
    enterprise = enterprise == 'True'
    quote_user = quote_user == 'True'

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
        starter_mode = []
    else:
        raise Exception("invalid starter mode: " + starter_mode)

    for runner in starter_mode:
        kill_all_processes()
    
        old_inst = installers.get(old_version,
                                  enterprise,
                                  Path(package_dir),
                                  publicip,
                                  quote_user)
        old_inst.calculate_package_names()
        
        new_inst = installers.get(version,
                                  enterprise,
                                  Path(package_dir),
                                  publicip,
                                  quote_user)
        new_inst.calculate_package_names()
    
        old_inst.install_package()

        if old_inst.check_service_up():
            old_inst.stop_service()
        stenv = getStarterenv(runner, old_inst.cfg)
        stenv.setup()
        stenv.run()
        stenv.post_setup()

        new_inst.upgrade_package()
        stenv.upgrade(new_inst.cfg)
        # end_test(inst.cfg, runner)
        stenv.shutdown()
        stenv.cleanup()
        kill_all_processes()
         
        new_inst.un_install_package()
        new_inst.check_uninstall_cleanup()
        new_inst.cleanup_system()


if __name__ == "__main__":
    run_test()
