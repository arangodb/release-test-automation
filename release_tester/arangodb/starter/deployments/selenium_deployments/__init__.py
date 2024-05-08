#!/usr/bin/env python3
""" baseclass to manage selenium UI tests """

from arangodb.starter.deployments import RunnerType
from arangodb.starter.deployments.selenium_deployments.sbase import SeleniumRunner, cleanup_temp_files

# pylint: disable=import-outside-toplevel disable=too-many-locals
# pylint: disable=too-many-branches disable=too-many-statements
# pylint: disable=too-many-return-statements disable=too-many-arguments
def init(
    runner_type: RunnerType,
    selenium_worker: str,
    selenium_driver_args: list,
    selenium_include_suites: list,
    testrun_name: str,
    ssl: bool,
) -> SeleniumRunner:
    """build selenium testcase for runner_type"""
    selenium_args = {
        "selenium_worker": selenium_worker,
        "selenium_driver_args": selenium_driver_args,
    }
    if runner_type == RunnerType.SINGLE:
        from arangodb.starter.deployments.selenium_deployments.single import (
            Single,
        )

        return Single(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.deployments.selenium_deployments.leaderfollower import (
            LeaderFollower,
        )

        return LeaderFollower(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.deployments.selenium_deployments.activefailover import (
            ActiveFailover,
        )

        return ActiveFailover(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.CLUSTER:
        from arangodb.starter.deployments.selenium_deployments.cluster import Cluster

        return Cluster(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.DC2DC:
        from arangodb.starter.deployments.selenium_deployments.dc2dc import Dc2Dc

        return Dc2Dc(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.DC2DCENDURANCE:
        from arangodb.starter.deployments.selenium_deployments.dc2dc_endurance import (
            Dc2DcEndurance,
        )

        return Dc2DcEndurance(selenium_args, testrun_name, ssl, selenium_include_suites)

    if runner_type == RunnerType.NONE:
        from arangodb.starter.deployments.selenium_deployments.none import NoStarter

        return NoStarter(selenium_args, testrun_name, ssl, selenium_include_suites)

    raise Exception("unknown starter type")
