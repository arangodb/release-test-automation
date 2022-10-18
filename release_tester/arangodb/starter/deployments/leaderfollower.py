#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

from tools.interact import prompt_user
from tools.killall import get_all_processes
from arangodb.starter.manager import StarterManager
from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner, RunnerProperties
import tools.loghelper as lh
from tools.asciiprint import print_progress as progress

from reporting.reporting_utils import step


class LeaderFollower(Runner):
    """this runs a leader / Follower setup with synchronisation"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        testrun_name: str,
        ssl: bool,
        use_auto_certs: bool,
    ):
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("LeaderFollower", 400, 500, False, ssl, use_auto_certs),
            selenium,
            selenium_driver_args,
            testrun_name,
        )

        self.leader_starter_instance = None
        self.follower_starter_instance = None
        self.passvoid = "leader"

        self.success = False
        ssl = "ssl://" if self.cfg.ssl else "tcp://"
        passvoid = self.passvoid
        self.checks = {
            "beforeReplJS": (
                "saving document before",
                """
db._create("testCollectionBefore");
db.testCollectionBefore.save({"hello": "world"})
""",
            ),
            "afterReplJS": (
                "saving document after the replication",
                """
db._create("testCollectionAfter");
db.testCollectionAfter.save({"hello": "world"})
""",
            ),
            "checkReplJS": (
                "checking documents",
                """
if (!db.testCollectionBefore) {
  throw new Error("before collection does not exist");
}
if (!db.testCollectionAfter) {
  throw new Error("after collection does not exist - replication failed");
}
if (!(db.testCollectionBefore.toArray()[0]["hello"] === "world")) {
  throw new Error("before not yet there?");
}
if (!(db.testCollectionAfter.toArray()[0]["hello"] === "world")) {
  throw new Error("after not yet there?");
}
""",
            ),
            "waitForReplState": (
                "Checking sync status",
                f"""
var internal = require("internal");
var replication = require("@arangodb/replication");
let compareTicks = replication.compareTicks;
var connectToLeader = function() {{
  arango.reconnect("{ssl}127.0.0.1:1235", "_system", "root", "{passvoid}");
  db._flushCache();
}};

var connectToFollower = function() {{
  arango.reconnect("{ssl}127.0.0.1:2346", "_system", "root", "{passvoid}");
  db._flushCache();
}};

let state = {{}};
var printed = false;
state.lastLogTick = replication.logger.state().state.lastUncommittedLogTick;

connectToFollower();
while (true) {{
  let followerState = replication.globalApplier.state();

  if (followerState.state.lastError.errorNum > 0) {{
    print("follower has errored:", JSON.stringify(followerState.state.lastError));
    throw new Error(JSON.stringify(followerState.state.lastError));
  }}

  if (!followerState.state.running) {{
    print("follower is not running");
    break;
  }}

  if (compareTicks(followerState.state.lastAppliedContinuousTick, state.lastLogTick) >= 0 ||
      compareTicks(followerState.state.lastProcessedContinuousTick, state.lastLogTick) >= 0) {{ // ||
    print("follower has caught up. state.lastLogTick:", state.lastLogTick, "followerState.lastAppliedContinuousTick:", followerState.state.lastAppliedContinuousTick, "followerState.lastProcessedContinuousTick:", followerState.state.lastProcessedContinuousTick);
    break;
  }}

  if (!printed) {{
    print("waiting for follower to catch up");
    printed = true;
  }}
  internal.wait(0.5, false);
}}
            """
                ),
        }

    def starter_prepare_env_impl(self):
        leader_opts = []
        follower_opts = []
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
            leader_tls_keyfile = self.cert_dir / Path("leader") / "tls.keyfile"
            follower_tls_keyfile = self.cert_dir / Path("follower") / "tls.keyfile"
            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(leader_tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            self.cert_op(
                [
                    "tls",
                    "keyfile",
                    "--cacert=" + str(self.certificate_auth["cert"]),
                    "--cakey=" + str(self.certificate_auth["key"]),
                    "--keyfile=" + str(follower_tls_keyfile),
                    "--host=" + self.cfg.publicip,
                    "--host=localhost",
                ]
            )
            leader_opts.append(f"--ssl.keyfile={leader_tls_keyfile}")
            follower_opts.append(f"--ssl.keyfile={follower_tls_keyfile}")

        self.leader_starter_instance = StarterManager(
            self.basecfg,
            self.basedir,
            "leader",
            mode="single",
            port=1234,
            expect_instances=[InstanceType.SINGLE],
            jwt_str="leader",
            moreopts=leader_opts,
        )
        self.leader_starter_instance.is_leader = True

        self.follower_starter_instance = StarterManager(
            self.basecfg,
            self.basedir,
            "follower",
            mode="single",
            port=2345,
            expect_instances=[InstanceType.SINGLE],
            jwt_str="follower",
            moreopts=follower_opts,
        )

    @step
    def check_data_impl_sh(self, arangosh, supports_foxx_tests):
        """ we want to see stuff is in sync! """
        print("Checking whether the follower has caught up")
        if not self.leader_starter_instance.execute_frontend(
                self.checks["waitForReplState"]):
            raise Exception("the follower would not catch up in time!")
        super().check_data_impl_sh(arangosh, supports_foxx_tests)

    def starter_run_impl(self):
        self.leader_starter_instance.run_starter()
        self.follower_starter_instance.run_starter()

        self.leader_starter_instance.detect_instances()
        self.follower_starter_instance.detect_instances()

        self.leader_starter_instance.detect_instance_pids()
        self.follower_starter_instance.detect_instance_pids()

        self.leader_starter_instance.set_passvoid(self.passvoid)
        # the replication will overwrite this passvoid anyways:
        self.follower_starter_instance.set_passvoid(self.passvoid)

        self.starter_instances = [
            self.leader_starter_instance,
            self.follower_starter_instance,
        ]

    def finish_setup_impl(self):
        # finish setup by starting the replications
        self.set_frontend_instances()

        self.checks["startReplJS"] = (
            "launching replication",
            """
print(
require("@arangodb/replication").setupReplicationGlobal({
    endpoint: "%s://127.0.0.1:%s",
    username: "root",
    password: "%s",
    verbose: false,
    includeSystem: true,
    incremental: true,
    autoResync: true
    }));
print("replication started")
process.exit(0);
"""
            % (
                self.get_protocol(),
                str(self.leader_starter_instance.get_frontend_port()),
                self.leader_starter_instance.get_passvoid(),
            ),
        )
        lh.subsubsection("prepare leader follower replication")
        arangosh_script = self.checks["beforeReplJS"]
        logging.info(str(self.leader_starter_instance.execute_frontend(arangosh_script)))

        lh.subsubsection("start leader follwer replication")
        arangosh_script = self.checks["startReplJS"]
        retval = self.follower_starter_instance.execute_frontend(arangosh_script)
        if not retval:
            raise Exception("Failed to start the replication using: %s %s" % (retval, str(self.checks["startReplJS"])))

        logging.info("Replication started successfully")

        logging.info("save document")
        arangosh_script = self.checks["afterReplJS"]
        logging.info(str(self.leader_starter_instance.execute_frontend(arangosh_script)))
        self.makedata_instances.append(self.leader_starter_instance)

    @step
    def test_setup_impl(self):
        logging.info("testing the leader/follower setup")
        tries = 30
        if not self.follower_starter_instance.execute_frontend(self.checks["checkReplJS"]):
            while tries:
                if self.follower_starter_instance.execute_frontend(self.checks["checkReplJS"]):
                    break
                progress(".")
                time.sleep(1)
                tries -= 1

        if not tries:
            if not self.follower_starter_instance.execute_frontend(self.checks["checkReplJS"]):
                raise Exception("replication didn't make it in 30s!")

        lh.subsection("leader/follower - check test data", "-")

        if self.selenium:
            self.selenium.test_after_install()
        # assert that data has been replicated
        self.follower_starter_instance.arangosh.read_only = True
        self.follower_starter_instance.supports_foxx_tests = False
        logging.info("Leader follower testing makedata on follower")
        self.makedata_instances.append(self.follower_starter_instance)
        self.make_data()
        if self.selenium:
            self.selenium.test_setup()

        logging.info("Leader follower setup successfully finished!")

    @step
    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.replace_binary_for_upgrade(self.new_cfg)
        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.command_upgrade()
            node.wait_for_upgrade()
            node.wait_for_upgrade_done_in_log()

        for node in [self.leader_starter_instance, self.follower_starter_instance]:
            node.detect_instances()
            node.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    @step
    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        self.progress(True, "step 1 - shut down instances")
        instances = [self.leader_starter_instance, self.follower_starter_instance]
        for node in instances:
            node.replace_binary_setup_for_upgrade(self.new_cfg)
            node.terminate_instance(True)
        self.progress(True, "step 2 - launch instances with the upgrade options set")
        for node in instances:
            print("launch")
            node.manually_launch_instances(
                [InstanceType.SINGLE],
                [
                    "--database.auto-upgrade",
                    "true",
                    "--javascript.copy-installation",
                    "true",
                ],
            )
        self.progress(True, "step 3 - launch instances again")
        for node in instances:
            node.respawn_instance()
        self.progress(True, "step 4 - detect system state")
        for node in instances:
            node.detect_instances()
            node.wait_for_version_reply()
        if self.selenium:
            self.selenium.test_after_install()

    @step
    def jam_attempt_impl(self):
        """run the replication fuzzing test"""
        logging.info("running the replication fuzzing test")
        # add instace where makedata will be run on
        self.tcp_ping_all_nodes()
        ret = self.leader_starter_instance.arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/replication/fuzz/replication-fuzz-global.js")),
            [],
            [self.follower_starter_instance.get_frontend().get_public_url("root:%s@" % self.passvoid)],
        )
        if not ret[0]:
            if not self.cfg.verbose:
                print(ret[1])
            raise Exception("replication fuzzing test failed")

        prompt_user(self.basecfg, "please test the installation.")
        if self.selenium:
            self.selenium.test_jam_attempt()

    @step
    def shutdown_impl(self):
        self.leader_starter_instance.terminate_instance()
        self.follower_starter_instance.terminate_instance()
        pslist = get_all_processes(False)
        if len(pslist) > 0:
            raise Exception("Not all processes terminated! [%s]" % str(pslist))
        logging.info("test ended")

    def before_backup_impl(self):
        """nothing to see here"""

    def after_backup_impl(self):
        """nothing to see here"""

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.leader_starter_instance.arango_importer,
            self.leader_starter_instance.arango_restore,
            self.leader_starter_instance.all_instances[0],
        )
