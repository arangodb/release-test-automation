#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import click
import tools.loghelper as lh
from common_options import zip_common_options
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set, RunProperties

from arangodb.starter.deployments import RunnerType, make_runner

# pylint: disable=W0703
def run_cleanup(zip_package, run_properties: RunProperties):
    """main"""

    installer_set = create_config_installer_set(
        ["3.3.3"],
        True,
        zip_package,
        "disabled",
        Path("/tmp/"),
        Path("/"),
        "127.0.0.1",
        "",
        False,
        False,
        run_properties
    )
    inst = installer_set[0][1]
    if inst.calc_config_file_name().is_file():
        inst.load_config()
        inst.cfg.interactive = False
        inst.stop_service()
        installer_set[0][0].set_directories(inst.cfg)
    kill_all_processes()
    kill_all_processes()
    starter_mode = [
        RunnerType.LEADER_FOLLOWER,
        RunnerType.ACTIVE_FAILOVER,
        RunnerType.CLUSTER,
        RunnerType.DC2DC,
    ]
    for runner_type in starter_mode:
        assert runner_type
        runner = make_runner(runner_type, False, "none", [], installer_set, run_properties)
        runner.cleanup()
    if inst.calc_config_file_name().is_file():
        try:
            inst.un_install_debug_package()
        except Exception:
            print("nothing to uninstall")
        try:
            inst.un_install_client_package()
        except Exception:
            print("nothing to uninstall")
        inst.un_install_server_package()
    else:
        print("Cannot uninstall package without config.yml!")
    inst.cleanup_system()


@click.command()
@zip_common_options
def run_test(zip_package):
    """Wrapper..."""
    lh.configure_logging(True)
    return run_cleanup(zip_package, RunProperties(False, False, False))


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    run_test()
