#!/usr/bin/env python3

""" Release testing script"""
import logging
from logging import info as log
from pathlib import Path

import click

from installers import arangosh
import installers.installers as installers
from installers.killall import kill_all_processes
from installers.starterenvironment import get as getStarterenv
from installers.starterenvironment import RunnerType

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--enterprise',
              default='True',
              help='Enterprise or community?')
@click.option('--mode',
              default='all',
              help='operation mode - [all|install|uninstall|tests].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
def run_test(version, package_dir, enterprise, mode, publicip):
    """ main """
    enterprise = enterprise == 'True'
    if mode not in ['all', 'install', 'tests', 'uninstall']:
        raise Exception("unsupported mode!")
    inst = installers.get(version,
                          enterprise,
                          Path(package_dir),
                          publicip)

    inst.calculate_package_names()
    kill_all_processes()
    if mode in ['all', 'install']:
        inst.install_package()
        inst.save_config()
        inst.stop_service()
        inst.broadcast_bind()
        inst.start_service()
        inst.check_installed_paths()
        inst.check_engine_file()
    else:
        inst.load_config()
    if mode in ['all', 'tests']:
        inst.stop_service()
        inst.start_service()

        sys_arangosh = arangosh.ArangoshExecutor(inst.cfg)

        if not sys_arangosh.js_version_check():
            log("Version Check failed!")
        input("Press Enter to continue")
        inst.stop_service()
        kill_all_processes()
        for runner in [RunnerType.LEADER_FOLLOWER,
                       RunnerType.ACTIVE_FAILOVER,
                       RunnerType.CLUSTER,
                       RunnerType.DC2DC]:
            stenv = getStarterenv(runner, inst.cfg)
            stenv.setup()
            stenv.run()
            stenv.post_setup()
            stenv.jam_attempt()
            input("Press Enter to continue")
            stenv.shutdown()
            stenv.cleanup()
            kill_all_processes()

    if mode in ['all', 'uninstall']:
        inst.un_install_package()
        inst.check_uninstall_cleanup()
        inst.cleanup_system()


if __name__ == "__main__":
    run_test()
