#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path
from tools.killall import get_all_processes
from arangodb.starter.manager import StarterManager
from arangodb.starter.environment.runner import Runner
import tools.loghelper as lh

class LeaderFollower(Runner):
    """ this runs a leader / Follower setup with synchronisation """
    def __init__(self, cfg):
        lh.section("Leader Follower Test")
        self.leader = None
        self.follower = None
        self.success = True
        self.basecfg = cfg
        self.basedir = Path('lf')
        self.cleanup()
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
if (!db.testCollectionBefore.toArray()[0]["hello"] === "world") {
  throw new Error("before not yet there?");
}
if (!db.testCollectionAfter.toArray()[0]["hello"] === "world") {
  throw new Error("after not yet there?");
}
""")}

    def setup(self):
        self.leader = StarterManager(self.basecfg,
                                     self.basedir / 'leader',
                                     mode='single',
                                     port=1234,
                                     moreopts=[])
        self.follower = StarterManager(self.basecfg,
                                       self.basedir / 'follower',
                                       mode='single',
                                       port=2345,
                                       moreopts=[])

    def run(self):
        self.leader.run_starter()
        self.follower.run_starter()
        self.leader.detect_instances()
        self.follower.detect_instances()
        self.leader.detect_instance_pids()
        self.follower.detect_instance_pids()

        #add new check
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
process.exit(0);
""" % (str(self.leader.get_frontend_port())))

        lh.subsubsection("prepare replication")
        arangosh_script = self.checks['beforeReplJS']
        logging.info(str(self.leader.execute_frontend(arangosh_script)))

        lh.subsubsection("start replication")
        arangosh_script = self.checks['startReplJS']
        retval = self.follower.execute_frontend(arangosh_script)
        if not retval:
            raise Exception("Failed to start the replication using: %s %s"%
                            (retval, str(self.checks['startReplJS'])))

        lh.subsubsection("add data (makedata) for replication")
        logging.info("Replication started successfully")
        self.leader.arangosh.create_test_data("lf (after starting replication)")


        logging.info("save document")
        arangosh_script = self.checks['afterReplJS']
        logging.info(str(self.leader.execute_frontend(arangosh_script)))


    def post_setup(self):
        logging.info("checking for the replication")

        count = 0
        while count < 30:
            if self.follower.execute_frontend(self.checks['checkReplJS']):
                break
            logging.info(".")
            time.sleep(1)
            count += 1
        if count > 29:
            raise Exception("replication didn't make it in 30s!")

        lh.subsection("leader/follower - check test data", "-")
        self.follower.arangosh.check_test_data("lf (after finishing setup)")

        logging.info("Leader follower setup successfully finished!")

    def upgrade(self, new_install_cfg):
        """ upgrade this installation """
        lh.subsection("upgrade test", "-")
        raise Exception("TODO!")

    def jam_attempt(self):
        lh.subsection("jam test", "-")
        pass

    def shutdown(self):
        self.leader.terminate_instance()
        self.follower.terminate_instance()
        pslist = get_all_processes()
        if len(pslist) > 0:
            raise Exception("Not all processes terminated! [%s]" % str(pslist))
        logging.info('test ended')
