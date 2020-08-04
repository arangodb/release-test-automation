#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner

logging.basicConfig(
    level=logging.DEBUG,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)

@click.command()
@click.option('--zip',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')

def run_test(zip):
    """ main """
    logging.getLogger().setLevel(logging.DEBUG)

    install_config = InstallerConfig('3.3.3',
                                     True,
                                     False,
                                     zip,
                                     Path("/tmp/"),
                                     "",

                                     "",
                                     False)
    inst = make_installer(install_config)

    kill_all_processes()
    inst.load_config()
    inst.cfg.interactive = False
    inst.stop_service()
    starter_mode = [RunnerType.LEADER_FOLLOWER,
                    RunnerType.ACTIVE_FAILOVER,
                    RunnerType.CLUSTER]  # ,
    #  RunnerType.DC2DC] here __init__ will create stuff, TODO.
    for runner_type in starter_mode:
        assert(runner_type)

        runner = make_runner(runner_type, inst.cfg, inst, None)
        runner.cleanup()

    inst.un_install_debug_package()
    inst.un_install_package()
    inst.cleanup_system()


if __name__ == "__main__":
    run_test()
