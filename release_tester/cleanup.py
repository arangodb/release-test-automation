#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import click
import tools.loghelper as lh
from common_options import zip_common_options
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner

def run_cleanup(zip_package, testrun_name: str = ""):
    """ main """

    install_config = InstallerConfig('3.3.3',
                                     True,
                                     False,
                                     False,
                                     zip_package,
                                     Path("/tmp/"),
                                     Path("/"),
                                     "127.0.0.1",
                                     "",
                                     False,
                                     False)
    inst = make_installer(install_config)

    if inst.calc_config_file_name().is_file():
        inst.load_config()
        inst.cfg.interactive = False
        inst.stop_service()
    kill_all_processes()
    kill_all_processes()
    starter_mode = [RunnerType.LEADER_FOLLOWER,
                    RunnerType.ACTIVE_FAILOVER,
                    RunnerType.CLUSTER]  # ,
    #  RunnerType.DC2DC] here __init__ will create stuff, TODO.
    for runner_type in starter_mode:
        assert runner_type

        runner = make_runner(runner_type,
                             'none', [],
                             inst.cfg, inst,
                             None, None,
                             testrun_name
                             )
        runner.cleanup()
    if inst.calc_config_file_name().is_file():
        try:
            inst.un_install_debug_package()
        except Exception:
            print('nothing to uninstall')
        inst.un_install_package()
    else:
        print('Cannot uninstall package without config.yml!')
    inst.cleanup_system()

@click.command()
@zip_common_options
def run_test(zip_package):
    """ Wrapper... """
    lh.configure_logging(True)
    return run_cleanup(zip_package)

if __name__ == "__main__":
# pylint: disable=E1120 # fix clickiness.
    run_test()
