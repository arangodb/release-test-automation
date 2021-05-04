#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from enum import Enum
import logging

from typing import Optional
from arangodb.starter.deployments.runner import Runner
from arangodb.installers.base import InstallerBase
from arangodb.installers import InstallerConfig

class RunnerType(Enum):
    """ dial which runner instance you want"""
    NONE = 0
    LEADER_FOLLOWER = 1
    ACTIVE_FAILOVER = 2
    CLUSTER = 3
    DC2DC = 4
    DC2DCENDURANCE = 5
    TESTING = 6

""" map strings """
runner_strings = {
    RunnerType.NONE: "none",
    RunnerType.LEADER_FOLLOWER: "Leader / Follower",
    RunnerType.ACTIVE_FAILOVER: "Active Failover",
    RunnerType.CLUSTER: "Cluster",
    RunnerType.DC2DC: "DC 2 DC",
    RunnerType.DC2DCENDURANCE: "DC 2 DC endurance",
    RunnerType.TESTING: "Testing"
}

#pylint: disable=import-outside-toplevel
def make_runner(runner_type: RunnerType,
                selenium_worker: str,
                selenium_driver_args: list,
                baseconfig: InstallerConfig,
                old_inst: InstallerBase,
                new_cfg: Optional[InstallerConfig] = None,
                new_inst: Optional[InstallerBase] = None,
                ) -> Runner:
    """ get an instance of the arangod runner - as you specify """

    assert runner_type, "no runner no cry?"
    assert baseconfig, "no base config?"
    assert old_inst, "no old version?"

    logging.debug("Factory for Runner of type: {0}".format(str(runner_type)))
    args = (runner_type, baseconfig, old_inst, new_cfg, new_inst, selenium_worker, selenium_driver_args)

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
        return NoStarter(*args)

    raise Exception("unknown starter type")
