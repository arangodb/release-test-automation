#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
from enum import Enum

class RunnerType(Enum):
    """ dial which runner instance you want"""
    LEADER_FOLLOWER = 1
    ACTIVE_FAILOVER = 2
    CLUSTER = 3
    DC2DC = 4


#pylint: disable=import-outside-toplevel
def get(typeof, baseconfig):
    """ get an instance of the arangod runner - as you specify """
    print("get!")
    if typeof == RunnerType.LEADER_FOLLOWER:
        from arangodb.starter.environment.leaderfollower import LeaderFollower
        return LeaderFollower(baseconfig)

    if typeof == RunnerType.ACTIVE_FAILOVER:
        from arangodb.starter.environment.activefailover import ActiveFailover
        return ActiveFailover(baseconfig)

    if typeof == RunnerType.CLUSTER:
        from arangodb.starter.environment.cluster import Cluster
        return Cluster(baseconfig)

    if typeof == RunnerType.DC2DC:
        from arangodb.starter.environment.dc2dc import Dc2Dc
        return Dc2Dc(baseconfig)
    raise Exception("unknown starter type")
