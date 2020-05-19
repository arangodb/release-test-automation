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

def run_test():
    """ main """
    logging.getLogger().setLevel(logging.DEBUG)

    inst = installers.get('0.0',
                          True,
                          False,
                          Path("/tmp/"),
                          "",
                          False)

    kill_all_processes()
    inst.load_config()
    inst.cfg.interactive = False
    inst.stop_service()
    starter_mode = [RunnerType.LEADER_FOLLOWER,
                    RunnerType.ACTIVE_FAILOVER,
                    RunnerType.CLUSTER]#,
                    #RunnerType.DC2DC] here __init__ will create stuff, TODO.
    for runner in starter_mode:
        stenv = getStarterenv(runner, inst.cfg)
        stenv.cleanup()

    inst.un_install_package()
    inst.cleanup_system()


if __name__ == "__main__":
    run_test()
