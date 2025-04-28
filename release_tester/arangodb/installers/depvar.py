#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from enum import Enum

from arangodb.installers import RunProperties

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

class RunnerProperties:
    """runner properties management class"""

    # pylint: disable=too-few-public-methods disable=too-many-arguments disable=too-many-branches disable=too-many-instance-attributes
    def __init__(
        self,
        rp: RunProperties,
        short_name: str,
        disk_usage_community: int,
        disk_usage_enterprise: int,
        supports_hotbackup: bool,
        no_arangods_non_agency: int,
    ):
        self.short_name = short_name
        self.testrun_name = rp.testrun_name
        self.disk_usage_community = disk_usage_community
        self.disk_usage_enterprise = disk_usage_enterprise
        self.supports_hotbackup = supports_hotbackup
        self.ssl = rp.ssl
        self.replication2 = rp.replication2
        self.use_auto_certs = rp.use_auto_certs
        self.force_one_shard = rp.force_one_shard
        self.create_oneshard_db = rp.create_oneshard_db
        self.no_arangods_non_agency = no_arangods_non_agency
        self.cluster_nodes = rp.cluster_nodes
