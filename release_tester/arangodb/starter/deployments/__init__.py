#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import logging
import platform
from typing import Optional

import semver

from arangodb.starter.deployments.runner import Runner
from arangodb.installers.depvar import RunnerProperties, RunnerType
from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig, RunProperties
from reporting.reporting_utils import step

IS_WINDOWS = platform.win32_ver()[0] != ""
IS_MAC = platform.mac_ver()[0] != ""



# pylint: disable=import-outside-toplevel disable=too-many-arguments disable=too-many-locals disable=too-many-function-args disable=too-many-branches
@step
def make_runner(
    runner_type: RunnerType,
    abort_on_error: bool,
    selenium_worker: str,
    selenium_driver_args: list,
    selenium_include_suites: list,
    installer_set: list,
    runner_properties: RunProperties,
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
        selenium_include_suites,
        runner_properties
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
