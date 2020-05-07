#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import sys
import signal
import click
import functools

from tools.killall import kill_all_processes
from tools.quote_user import end_test
from arangodb.sh import ArangoshExecutor
import arangodb.installers as installers
from arangodb.starter.environment import get as getStarterenv
from arangodb.starter.environment import RunnerType

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
ON_WINDOWS = (sys.platform == 'win32')
SIGNALS = {
    signal.SIGINT: 'SIGINT',
    signal.SIGTERM: 'SIGTERM',
}
if ON_WINDOWS:
    SIGNALS[signal.SIGBREAK] = 'SIGBREAK'

def term(proc):
    """Send a SIGTERM/SIGBREAK to *proc* and wait for it to terminate."""
    if ON_WINDOWS:
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        proc.terminate()
    proc.wait()
def cleanup(name, child, signum, frame):
    """Stop the sub=process *child* if *signum* is SIGTERM. Then terminate."""
    try:
        print('%s got a %s' % (name, SIGNALS[signum]))
        if child and (ON_WINDOWS or signum != signal.SIGINT):
            # Forward SIGTERM on Linux or any signal on Windows
            term(child)
    except:
        traceback.print_exc()
    #finally:
        # sys.exit()

@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose', help='switch starter to verbose logging mode.')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--enterprise',
              default='True',
              help='Enterprise or community?')
@click.option('--quote_user',
              default='True',
              help='wait for the user to hit Enter?')
@click.option('--mode',
              default='all',
              help='operation mode - [all|install|uninstall|tests].')
@click.option('--starter_mode',
              default='all',
              help='which starter environments to start - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')
def run_test(version, verbose, package_dir, enterprise, quote_user, mode, starter_mode, publicip):
    """ main """
    enterprise = enterprise == 'True'
    quote_user = quote_user == 'True'
    verbose = verbose == 'True'
    if mode not in ['all', 'install', 'system', 'tests', 'uninstall']:
        raise Exception("unsupported mode %s!" % mode)
    inst = installers.get(version,
                          verbose,
                          enterprise,
                          Path(package_dir),
                          publicip,
                          quote_user)

    inst.calculate_package_names()
    kill_all_processes()
    if mode in ['all', 'install']:
        inst.install_package()
        inst.check_installed_files()
        inst.save_config()
        if inst.check_service_up():
            inst.stop_service()
        inst.broadcast_bind()
        inst.start_service()
        inst.check_installed_paths()
        inst.check_engine_file()
    else:
        inst.load_config()
        inst.cfg.quote_user = quote_user
    if mode in ['all', 'system']:
        if inst.check_service_up():
            inst.stop_service()
        inst.start_service()

        sys_arangosh = ArangoshExecutor(inst.cfg)

        if not sys_arangosh.js_version_check():
            logging.info("Version Check failed!")
        end_test(inst.cfg, 'system package')

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
