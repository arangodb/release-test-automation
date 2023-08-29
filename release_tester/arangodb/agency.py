#!/usr/bin/env python3
""" Abstract communication with the agency """
import datetime
import platform
import time

import requests

from arangodb.instance import InstanceType
from reporting.reporting_utils import step

WINVER = platform.win32_ver()

class Agency():
    """ abstract management of the agency """
    def __init__(self, runner):
        self.runner = runner
        self.starter_instances = runner.starter_instances

    @step
    def trigger_leader_relection(self, old_leader):
        """halt one agent to trigger an agency leader re-election"""
        self.runner.progress(True, "AGENCY pausing leader to trigger a failover\n%s" % repr(old_leader))
        old_leader.suspend_instance()
        time.sleep(1)
        count = 0
        while True:
            new_leader = self.get_leader()
            if old_leader != new_leader:
                self.runner.progress(True, "AGENCY failover has happened")
                break
            if count == 500:
                raise Exception("agency failoverdidn't happen in 5 minutes!")
            time.sleep(1)
            count += 1
        old_leader.resume_instance()
        if WINVER[0]:
            leader_mgr = None
            for starter_mgr in self.starter_instances:
                if starter_mgr.have_this_instance(old_leader):
                    leader_mgr = starter_mgr

            old_leader.kill_instance()
            time.sleep(5)  # wait for the starter to respawn it...
            old_leader.detect_pid(leader_mgr.instance.pid)

    @step
    def get_leader(self):
        """get the agent that has the latest "serving" line"""
        # please note: dc2dc has two agencies, this function cannot
        # decide between the two of them, and hence may give you
        # the follower DC agent as leader.
        agency = []
        for starter_mgr in self.starter_instances:
            agency += starter_mgr.get_agents()
        leader = None
        leading_date = datetime.datetime(1970, 1, 1, 0, 0, 0)
        for agent in agency:
            agent_leading_date = agent.search_for_agent_serving()
            if agent_leading_date > leading_date:
                leading_date = agent_leading_date
                leader = agent
        return leader

    @step
    def get_leader_starter_instance(self):
        """get the starter instance that manages the current agency leader"""
        leader = None
        leading_date = datetime.datetime(1970, 1, 1, 0, 0, 0)
        for starter_mgr in self.starter_instances:
            agents = starter_mgr.get_agents()
            for agent in agents:
                agent_leading_date = agent.search_for_agent_serving()
                if agent_leading_date > leading_date:
                    leading_date = agent_leading_date
                    leader = starter_mgr
        return leader

    @step
    def acquire_dump(self):
        """turns on logging on the agency"""
        print("Dumping agency")
        commands = [
            {
                "URL": "/_api/agency/config",
                "method": requests.get,
                "basefn": "agencyConfig",
                "body": None,
            },
            {
                "URL": "/_api/agency/state",
                "method": requests.get,
                "basefn": "agencyState",
                "body": None,
            },
            {
                "URL": "/_api/agency/read",
                "method": requests.post,
                "basefn": "agencyPlan",
                "body": '[["/"]]',
            },
        ]
        for starter_mgr in self.starter_instances:
            try:
                for cmd in commands:
                    reply = starter_mgr.send_request(
                        InstanceType.AGENT,
                        cmd["method"],
                        cmd["URL"],
                        cmd["body"],
                        timeout=10,
                    )
                    print(reply)
                    count = 0
                    for repl in reply:
                        (starter_mgr.basedir / f"{cmd['basefn']}_{count}.json").write_text(repl.text)
                        count += 1
            except requests.exceptions.RequestException as ex:
                # We skip one starter and all its agency dump attempts now.
                print("Error during an agency dump: " + str(ex))
