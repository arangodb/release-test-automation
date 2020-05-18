#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import sys
import click
from tools.killall import kill_all_processes
from tools.interact import end_test
from arangodb.sh import ArangoshExecutor
import arangodb.installers as installers
from arangodb.starter.environment import get as getStarterenv
from arangodb.starter.environment import RunnerType
import tools.loghelper as lh
import tools.errorhelper as eh
import obi.util

logging.basicConfig(
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)

@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose',
              is_flag=True,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
              help='wait for the user to hit Enter?')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--mode',
              default='all',
              help='operation mode - [all|install|uninstall|tests].')
@click.option('--starter-mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')


def run_test(version, verbose, package_dir, enterprise,
             interactive, mode, starter_mode, publicip):
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("package directory: " + str(package_dir))
    print("mode: " + str(mode))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    if mode not in ['all', 'install', 'system', 'tests', 'uninstall']:
        raise Exception("unsupported mode %s!" % mode)

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    inst = installers.get(version,
                          verbose,
                          enterprise,
                          Path(package_dir),
                          publicip,
                          interactive)

    inst.calculate_package_names()
    kill_all_processes()
    if mode in ['all', 'install']:
        lh.section("INSTALLING PACKAGE")
        inst.install_package()
        lh.section("CHECKING FILES")
        inst.check_installed_files()
        lh.section("SAVING CONFIG")
        inst.save_config()
        lh.section("CHECKING IF SERVICE IS UP")
        if inst.check_service_up():
            lh.section("STOPPING SERVICE")
            inst.stop_service()
        inst.broadcast_bind()
        lh.section("STARTING SERVICE")
        inst.start_service()
        inst.check_installed_paths()
        inst.check_engine_file()
    else:
        inst.load_config()
        inst.cfg.interactive = interactive
    if mode in ['all', 'system']:
        if inst.check_service_up():
            inst.stop_service()
        inst.start_service()

        sys_arangosh = ArangoshExecutor(inst.cfg)

        if not sys_arangosh.js_version_check():
            logging.info("Version Check failed!")
            eh.prompt_to_continue(inst.cfg.interactive)

        end_test(inst.cfg, 'Installation of system package')

    if mode in ['all', 'tests']:
        if inst.check_service_up():
            inst.stop_service()
        kill_all_processes()
        print(starter_mode)

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
            starter_mode = []
        else:
            raise Exception("invalid starter mode: " + starter_mode)
        for runner in starter_mode:
            stenv = getStarterenv(runner, inst.cfg)
            stenv.setup()
            stenv.run()
            stenv.post_setup()
            stenv.jam_attempt()
            end_test(inst.cfg, runner)
            stenv.shutdown()
            stenv.cleanup()
            kill_all_processes()

    if mode in ['all', 'uninstall']:
        inst.un_install_package()
        inst.check_uninstall_cleanup()
        inst.cleanup_system()


if __name__ == "__main__":
    run_test()
