#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

from arangodb.starter.manager import StarterManager
from arangodb.starter.environment.runner import Runner

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')


class LeaderFollower(Runner):
    """ this runs a leader / Follower setup with synchronisation """
    def __init__(self, cfg):
        logging.info("x"*80)
        logging.info("xx           Leader Follower Test      ")
        logging.info("x"*80)
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
        self.leader.detect_instance_pids()
        self.follower.detect_instance_pids()

        logging.info(str(self.leader.execute_frontend(
            self.checks['beforeReplJS'])))
        self.checks['startReplJS'] = (
            "launching replication",
            """
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "tcp://127.0.0.1:%d",
    username: "root",
    password: "",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    });
""" % (self.leader.get_frontend_port()))
        logging.info(str(self.follower.execute_frontend(
            self.checks['startReplJS'])))
        self.leader.arangosh.create_test_data()
        logging.info(str(self.leader.execute_frontend(
            self.checks['afterReplJS'])))
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

        self.follower.arangosh.check_test_data()

        logging.info("all OK!")

    def jam_attempt(self):
        pass

    def shutdown(self):
        self.leader.kill_instance()
        self.follower.kill_instance()
        logging.info('test ended')
