#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path
from tools.killall import get_all_processes
from arangodb.starter.manager import StarterManager
from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

class LeaderFollower(Runner):
    """ this runs a leader / Follower setup with synchronisation """
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst):
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst, 'lf')

        self.leader_starter_instance = None
        self.follower_starter_instance = None

        self.success = False
        self.checks = {
            "beforeReplJS": (
                "saving document before",
                """
db._create("testCollectionBefore");
db.testCollectionBefore.save({"hello": "world"})
"""),
            "afterReplJS": (
                "saving document after the replication",
                """
db._create("testCollectionAfter");
db.testCollectionAfter.save({"hello": "world"})
"""),
            "checkReplJS": (
                "checking documents",
                """
if (!db.testCollectionBefore) {
  throw new Error("before collection does not exist");
}
if (!db.testCollectionAfter) {
  throw new Error("after collection does not exist - replication failed");
}
if (!db.testCollectionBefore.toArray()[0]["hello"] === "world") {
  throw new Error("before not yet there?");
}
if (!db.testCollectionAfter.toArray()[0]["hello"] === "world") {
  throw new Error("after not yet there?");
}
""")}

    def starter_prepare_env_impl(self):
        self.leader_starter_instance = StarterManager(
            self.cfg, self.basedir, 'leader',
            mode='single', port=1234,
            expect_instances=[
                InstanceType.single
            ],
            moreopts=[])
        self.leader_starter_instance.is_leader = True

        self.follower_starter_instance = StarterManager(
            self.cfg, self.basedir, 'follower',
            mode='single', port=2345,
            expect_instances=[
                InstanceType.single
            ],
            moreopts=[])

    def starter_run_impl(self):
        self.leader_starter_instance.run_starter()
        self.follower_starter_instance.run_starter()

        self.leader_starter_instance.detect_instances()
        self.follower_starter_instance.detect_instances()

        self.leader_starter_instance.detect_instance_pids()
        self.follower_starter_instance.detect_instance_pids()

    def finish_setup_impl(self):
        # finish setup by starting the replications

        self.checks['startReplJS'] = (
            "launching replication",
            """
print(
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "tcp://127.0.0.1:%s",
    username: "root",
    password: "",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    }));
print("replication started")
process.exit(0);
""" % (str(self.leader_starter_instance.get_frontend_port())))

        lh.subsubsection("prepare leader follower replication")
        arangosh_script = self.checks['beforeReplJS']
        logging.info(str(self.leader_starter_instance.execute_frontend(arangosh_script)))

        lh.subsubsection("start leader follwer replication")
        arangosh_script = self.checks['startReplJS']
        retval = self.follower_starter_instance.execute_frontend(arangosh_script)
        if not retval:
            raise Exception("Failed to start the replication using: %s %s"%
                            (retval, str(self.checks['startReplJS'])))

        logging.info("Replication started successfully")

        logging.info("save document")
        arangosh_script = self.checks['afterReplJS']
        logging.info(str(self.leader_starter_instance.execute_frontend(arangosh_script)))

        # add instace where makedata will be run on
        self.makedata_instances.append(self.leader_starter_instance)
        if not self.leader_starter_instance.arangosh.run_in_arangosh(
            Path('test_data/tests/js/server/replication/fuzz/replication-fuzz-global.js'),
            [],
            [self.follower_starter_instance.get_frontend().get_public_url('')]
            ):
            raise Exception("replication fuzzing test failed")

    def test_setup_impl(self):
        logging.info("testing the leader/follower setup")
        tries = 30
        if not self.follower_starter_instance.execute_frontend(self.checks['checkReplJS']):
            while tries:
                if self.follower_starter_instance.execute_frontend(self.checks['checkReplJS'], False):
                    break
                progress(".")
                time.sleep(1)
                tries -= 1

        if not tries:
            if not self.follower_starter_instance.execute_frontend(self.checks['checkReplJS']):
                raise Exception("replication didn't make it in 30s!")

        lh.subsection("leader/follower - check test data", "-")

        #assert that data has been replicated
        self.follower_starter_instance.arangosh.read_only = True
        self.makedata_instances.append(self.follower_starter_instance)
        self.make_data()

        logging.info("Leader follower setup successfully finished!")

    def supports_backup_impl(self):
        return False

    def upgrade_arangod_version_impl(self):
        """ upgrade this installation """
        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.replace_binary_for_upgrade(self.new_cfg)
        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.command_upgrade()
            node.wait_for_upgrade()
            node.wait_for_upgrade_done_in_log()

        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.detect_instances()
            node.wait_for_version_reply()

    def jam_attempt_impl(self):
        logging.info("not implemented skipping")
        

    def shutdown_impl(self):
        self.leader_starter_instance.terminate_instance()
        self.follower_starter_instance.terminate_instance()
        pslist = get_all_processes()
        if len(pslist) > 0:
            raise Exception("Not all processes terminated! [%s]" % str(pslist))
        logging.info('test ended')
