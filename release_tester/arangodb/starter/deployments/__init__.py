#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from enum import Enum
import logging
import platform
from typing import Optional

import semver

from arangodb.starter.deployments.runner import Runner
from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig, RunProperties
from reporting.reporting_utils import step

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_MAC = platform.mac_ver()[0] != ""


class RunnerType(Enum):
    """dial which runner instance you want"""

    NONE = 0
    SINGLE = 1
    LEADER_FOLLOWER = 2
    ACTIVE_FAILOVER = 3
    CLUSTER = 4
    DC2DC = 5
    DC2DCENDURANCE = 6
    TESTING = 7


runner_strings = {
    RunnerType.NONE: "none",
    RunnerType.SINGLE: "Single Server",
    RunnerType.LEADER_FOLLOWER: "Leader / Follower",
    RunnerType.ACTIVE_FAILOVER: "Active Failover",
    RunnerType.CLUSTER: "Cluster",
    RunnerType.DC2DC: "DC 2 DC",
    RunnerType.DC2DCENDURANCE: "DC 2 DC endurance",
    RunnerType.TESTING: "Testing",
}

STARTER_MODES = {
    "all": [
        RunnerType.SINGLE,
        RunnerType.LEADER_FOLLOWER,
        RunnerType.ACTIVE_FAILOVER,
        RunnerType.CLUSTER,
        RunnerType.DC2DC,
    ],
    "SG": [RunnerType.SINGLE],
    "LF": [RunnerType.LEADER_FOLLOWER],
    "AFO": [RunnerType.ACTIVE_FAILOVER],
    "CL": [RunnerType.CLUSTER],
    "DC": [RunnerType.DC2DC],
    "DCendurance": [RunnerType.DC2DCENDURANCE],
    "none": [RunnerType.NONE],
}

# pylint: disable=import-outside-toplevel disable=too-many-arguments disable=too-many-locals disable=too-many-function-args disable=too-many-branches
@step
def make_runner(
    runner_type: RunnerType,
    abort_on_error: bool,
    selenium_worker: str,
    selenium_driver_args: list,
    installer_set: list,
    runner_properties: RunProperties,
    use_auto_certs: bool = True,
) -> Runner:
    """get an instance of the arangod runner - as you specify"""
    # pylint: disable=too-many-return-statements
    assert runner_type, "no runner no cry?"
    assert len(installer_set) > 0, "no base config?"
    for one_installer_set in installer_set:
        assert len(one_installer_set) == 2, "no complete object config?"

    # Configure Chrome to accept self-signed SSL certs and certs signed by unknown CA.
    # FIXME: Add custom CA to Chrome to properly validate server cert.
    if runner_properties.ssl:
        selenium_driver_args += ("ignore-certificate-errors",)

    logging.debug("Factory for Runner of type: {0}".format(str(runner_type)))
    msg = ""
    if runner_type == RunnerType.ACTIVE_FAILOVER and installer_set[len(installer_set) - 1][
        1
    ].cfg.semver > semver.VersionInfo.parse("3.11.99"):
        runner_type = RunnerType.NONE
        msg = "Active failover not supported for these versions"

    if runner_type == RunnerType.DC2DC:
        if not installer_set[len(installer_set) - 1][1].cfg.enterprise:
            runner_type = RunnerType.NONE
            msg = "DC2DC deployment is not supported in community edition."
        elif IS_WINDOWS:
            runner_type = RunnerType.NONE
            msg = "DC2DC deployment is not supported on Windows."
        elif IS_MAC:
            runner_type = RunnerType.NONE
            msg = "DC2DC deployment is not supported on MacOS."
        elif installer_set[len(installer_set) - 1][1].cfg.semver > semver.VersionInfo.parse("3.11.99"):
            runner_type = RunnerType.NONE
            msg = "DC2DC deployment not supported on version 3.12 and newer."

    args = (
        runner_type,
        abort_on_error,
        installer_set,
        selenium_worker,
        selenium_driver_args,
        runner_properties.testrun_name,
        runner_properties.ssl,
        runner_properties.replication2,
        use_auto_certs,
    )

    if runner_type == RunnerType.SINGLE:
        from arangodb.starter.deployments.single import Single

        return Single(*args)

    if runner_type == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.deployments.leaderfollower import LeaderFollower

        return LeaderFollower(*args)

    if runner_type == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.deployments.activefailover import ActiveFailover

        return ActiveFailover(*args)

    if runner_type == RunnerType.CLUSTER:
        from arangodb.starter.deployments.cluster import Cluster

        return Cluster(*args)

    if runner_type == RunnerType.DC2DC:
        from arangodb.starter.deployments.dc2dc import Dc2Dc

        return Dc2Dc(*args)

    if runner_type == RunnerType.DC2DCENDURANCE:
        from arangodb.starter.deployments.dc2dc_endurance import Dc2DcEndurance

        return Dc2DcEndurance(*args)

    if runner_type == RunnerType.NONE:
        from arangodb.starter.deployments.none import NoStarter

        ret = NoStarter(*args)
        ret.msg = msg
        return ret

    raise Exception("unknown starter type")
