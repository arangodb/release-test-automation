#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import sys
import re
import click
from common_options import very_common_options, common_options
from tools.killall import kill_all_processes
from arangodb.installers import create_config_installer_set, RunProperties, HotBackupCliCfg, InstallerBaseConfig
from arangodb.starter.deployments.cluster_perf import ClusterPerf
from arangodb.starter.deployments import RunnerType
import tools.loghelper as lh


@click.command()
@click.option(
    "--mode",
    type=click.Choice(
        [
            "all",
            "install",
            "uninstall",
            "tests",
        ]
    ),
    default="all",
    help="operation mode.",
)
@click.option(
    "--scenario",
    default="scenarios/cluster_replicated.yml",
    help="test configuration yaml file, default written & exit if not there.",
)
@click.option("--frontends", multiple=True, help="Connection strings of remote clusters")
@very_common_options
@common_options(support_old=False)
def main(**kwargs):
    """ main """
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path(kwargs['test_data_dir'])
    kwargs['alluredir'] = Path(kwargs['alluredir'])

    kwargs['hb_cli_cfg'] = HotBackupCliCfg.from_dict(**kwargs)
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)

    test_driver = TestDriver(**kwargs)

    do_install = mode in ["all", "install"]
    do_uninstall = mode in ["all", "uninstall"]

    lh.section("startup")
    # pylint: disable=too-many-function-args
    props = RunProperties(kwargs['enterprise'],
                          kwargs['encryption_at_rest'],
                          kwargs['ssl'],
                          "perf")
    #installers = create_config_installer_set(
    #    [new_version],
    #    verbose,
    #    zip_package,
    #    HotBackupCliCfg(hot_backup,
    #                    hb_provider,
    #                    hb_storage_path_prefix,
    #                    hb_aws_access_key_id,
    #                    hb_aws_secret_access_key,
    #                    hb_aws_region,
    #                    hb_aws_acl),
    #    Path(package_dir),
    #    Path(test_data_dir),
    #    mode,
    #    publicip,
    #    interactive,
    #    False,
    #    props
    #)
    #
    #inst = installers[0][1]
    #lh.section("configuration")
    #print(
    #    """
    #mode: {mode}
    #{cfg_repr}
    #""".format(
    #        **{"mode": str(mode), "cfg_repr": repr(installers[0][0])}
    #    )
    #)
    #
    #split_host = re.compile(r"([a-z]*)://([0-9.:]*):(\d*)")
    #
    #if len(frontends) > 0:
    #    for frontend in frontends:
    #        print("remote")
    #        host_parts = re.split(split_host, frontend)
    #        inst.cfg.add_frontend(host_parts[1], host_parts[2], host_parts[3])
    #inst.cfg.scenario = Path(scenario)
    #runner = ClusterPerf(
    #    RunnerType.CLUSTER,
    #    abort_on_error,
    #    installers,
    #    selenium,
    #    selenium_driver_args,
    #    "perf",
    #    ssl,
    #    use_auto_certs,
    #)
    #runner.do_install = do_install
    #runner.do_uninstall = do_uninstall
    #failed = False
    #if not runner.run():
    #    failed = True
    #
    #if len(frontends) == 0:
    #    kill_all_processes()

    return 0 if not failed else 1


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(run_test())
