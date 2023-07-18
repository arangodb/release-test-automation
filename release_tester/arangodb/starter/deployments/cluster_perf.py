#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
import os
from pathlib import Path
from queue import Queue, Empty
from threading import Thread

from reporting.reporting_utils import step
import psutil
# import statsd
import yaml

from arangodb.instance import InstanceType
from arangodb.starter.deployments.runner import Runner, RunnerProperties
from arangodb.starter.deployments.cluster import Cluster

from tools.asciiprint import print_progress as progress
import tools.interact as ti
import tools.loghelper as lh
# from tools.prometheus import set_prometheus_jwt
from tools.timestamp import timestamp

# pylint: disable=global-statement
class TestConfig:
    """this represents one tests configuration"""

    # pylint: disable=too-many-instance-attributes disable=too-few-public-methods
    def __init__(self):
        self.parallelity = 3
        self.db_count = 100
        self.db_count_chunks = 5
        self.min_replication_factor = 2
        self.max_replication_factor = 3
        self.data_multiplier = 4
        self.collection_multiplier = 1
        self.launch_delay = 1.3
        self.single_shard = False
        self.db_offset = 0
        self.progressive_timeout = 10000
        self.hot_backup = False

# pylint: disable=global-variable-not-assigned
#statsdc = statsd.StatsClient("localhost", 8125)
RESULTS_TXT = None
OTHER_SH_OUTPUT = None


def result_line(wait, line, params):
    """get one result line"""
    global OTHER_SH_OUTPUT, RESULTS_TXT
    if isinstance(line, tuple):
        print(line[0])
        if line[0].startswith(b"#"):
            str_line = str(line[0])[6:-3]
            segments = str_line.split(",")
            if len(segments) < 3:
                print("n/a")
            else:
                str_line = ",".join(segments) + "\n"
                print(str_line)
                RESULTS_TXT.write(str_line)
                # statsdc.timing(segments[0], float(segments[2]))
        else:
            # OTHER_SH_OUTPUT.write(line[1].get_endpoint() + " - " + str(line[0]) + "\n")
            #statsdc.incr("completed")
            return False
    return True


def makedata_runner(queue, resq, arangosh, progressive_timeout):
    """operate one makedata instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print("starting my task! " + str(job["args"]))
            res = arangosh.create_test_data("xx",
                                            args=job["args"],
                                            result_line_handler=result_line,
                                            progressive_timeout=progressive_timeout)
            if not res[0]:
                print("error executing test - giving up.")
                print(res[1])
                resq.put(1)
                break
            resq.put(res)
        except Empty:
            print("No more work!")
            resq.put(-1)
            break


class ClusterPerf(Runner):
    """this launches a cluster setup"""

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
        global OTHER_SH_OUTPUT, RESULTS_TXT
        cfg = installer_set[0][1].cfg
        if not cfg.scenario.exists():
            cfg.scenario.write_text(yaml.dump(TestConfig()))
            raise Exception("have written %s with default config" % str(cfg.scenario))

        with open(cfg.scenario, encoding='utf8', mode="r") as fileh:
            self.scenario = yaml.load(fileh, Loader=yaml.Loader)

        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("CLUSTER", 400, 600, False, ssl, use_auto_certs, 6),
            selenium,
            selenium_driver_args,
            testrun_name,
        )
        self.success = False
        # self.cfg.frontends = []
        self.starter_instances = []
        self.jwtdatastr = str(timestamp())
        self.create_test_collection = ""
        self.min_replication_factor = 2
        RESULTS_TXT = Path("/tmp/results.txt").open("w", encoding='utf8')
        OTHER_SH_OUTPUT = Path("/tmp/errors.txt").open("w", encoding='utf8')

    def starter_prepare_env_impl(self):
        self.cfg.index = 0

        # pylint: disable=import-outside-toplevel
        if self.remote:
            from arangodb.starter.manager import StarterNonManager as StarterManager
        else:
            from arangodb.starter.manager import StarterManager
        self.create_test_collection = (
            "create test collection",
            """
db._create("testCollection",  { numberOfShards: 6, replicationFactor: 2});
db.testCollection.save({test: "document"})
""",
        )

        node1_opts = []
        node2_opts = ["--starter.join", "127.0.0.1:9528"]
        node3_opts = ["--starter.join", "127.0.0.1:9528"]
        if self.cfg.ssl and not self.cfg.use_auto_certs:
            self.create_tls_ca_cert()
            node1_tls_keyfile = self.cert_dir / Path("node1") / "tls.keyfile"
            node2_tls_keyfile = self.cert_dir / Path("node2") / "tls.keyfile"
            node3_tls_keyfile = self.cert_dir / Path("node3") / "tls.keyfile"

            for keyfile in [node1_tls_keyfile, node2_tls_keyfile, node3_tls_keyfile]:
                self.generate_keyfile(keyfile)

            node1_opts.append(f"--ssl.keyfile={node1_tls_keyfile}")
            node2_opts.append(f"--ssl.keyfile={node2_tls_keyfile}")
            node3_opts.append(f"--ssl.keyfile={node3_tls_keyfile}")

        def add_starter(name, port, opts):
            self.starter_instances.append(
                StarterManager(
                    self.cfg,
                    self.basedir,
                    name,
                    mode="cluster",
                    jwt_str=self.jwtdatastr,
                    port=port,
                    expect_instances=[
                        InstanceType.AGENT,
                        InstanceType.COORDINATOR,
                        InstanceType.DBSERVER,
                    ],
                    moreopts=opts,
                )
            )

        add_starter("node1", 9528, node1_opts)
        add_starter("node2", 9628, node2_opts)
        add_starter("node3", 9728, node3_opts)
         # += ['--agents.agency.election-timeout-min=5',
         #     '--agents.agency.election-timeout-max=10',]
        for instance in self.starter_instances:
            instance.is_leader = True

    def make_data_impl(self):
        pass  # we do this later.

    def check_data_impl_sh(self, arangosh, supports_foxx_tests):
        pass  # we don't care

    def check_data_impl(self):
        pass

    def starter_run_impl(self):
        lh.subsection("instance setup")
        # if self.remote:
        #    logging.info("running remote, skipping")
        #    return
        for manager in self.starter_instances:
            logging.info("Spawning instance")
            manager.run_starter()

        logging.info("waiting for the starters to become alive")
        not_started = self.starter_instances[:]  # This is a explicit copy
        count = 0
        while not_started:
            logging.debug("waiting for mananger with logfile:" + str(not_started[-1].log_file))
            if not_started[-1].is_instance_up():
                not_started.pop()
            progress(".")
            time.sleep(1)
            count += 1
            if count > 120:
                raise Exception("Cluster installation didn't come up in two minutes!")

        logging.info("waiting for the cluster instances to become alive")
        for node in self.starter_instances:
            node.detect_instances()
            node.detect_instance_pids()
            # self.cfg.add_frontend('http', self.cfg.publicip, str(node.get_frontend_port()))

        logging.info("instances are ready - JWT: " + self.starter_instances[0].get_jwt_header())
        count = 0
        for node in self.starter_instances:
            node.set_passvoid("cluster", count == 0)
            count += 1
        self.passvoid = "cluster"

    def finish_setup_impl(self):
        if self.remote:
            logging.info("running remote, skipping")
            return
        self.makedata_instances = self.starter_instances[:]
        self.set_frontend_instances()
        # self.agency_set_debug_logging()
        # self.dbserver_set_debug_logging()
        # self.coordinator_set_debug_logging()

        # set_prometheus_jwt(self.starter_instances[0].get_jwt_header())

    def test_setup_impl(self):
        pass

    def after_makedata_check(self):
        pass

    def test_setup_impl(self):
        pass

    def wait_for_restore_impl(self, backup_starter):
        pass

    def upgrade_arangod_version_impl(self):
        """rolling upgrade this installation"""
        # self.agency_set_debug_logging()
        bench_instances = []
        if self.cfg.stress_upgrade:
            bench_instances.append(self.starter_instances[0].launch_arangobench("cluster_upgrade_scenario_1"))
            bench_instances.append(self.starter_instances[1].launch_arangobench("cluster_upgrade_scenario_2"))
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg)

        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        self.starter_instances[1].command_upgrade()
        if self.selenium:
            self.selenium.test_wait_for_upgrade()  # * 5s
        self.starter_instances[1].wait_for_upgrade(300)
        if self.cfg.stress_upgrade:
            bench_instances[0].wait()
            bench_instances[1].wait()
        for node in self.starter_instances:
            node.detect_instance_pids()

    def upgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        lh.subsubsection("wait for all shards to be in sync - Manual upgrade")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ['true'],
        )
        if not retval:
            raise Exception(
                "Failed to ensure the cluster is in sync: %s" % (retval)
            )
        print("all in sync.")
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg, False)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        # fmt: off
        self.progress(True, "step 2 - upgrade agents")
        for node in self.starter_instances:
            node.upgrade_instances(
                [
                    InstanceType.AGENT
                ], [
                    '--database.auto-upgrade', 'true',
                    '--log.foreground-tty', 'true'
                ],
                # mitigate 3.6x agency shutdown issues:
                self.cfg.version >= arangoversions['370'])
        self.progress(True, "step 3 - upgrade db-servers")
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.DBSERVER
            ], ['--database.auto-upgrade', 'true',
                '--log.foreground-tty', 'true'])
        self.progress(True, "step 4 - coordinator upgrade")
        # now the new cluster is running. we will now run the coordinator upgrades
        for node in self.starter_instances:
            logging.info("upgrading coordinator instances\n" + str(node))
            node.upgrade_instances([
                InstanceType.COORDINATOR
            ], [
                '--database.auto-upgrade', 'true',
                '--javascript.copy-installation', 'true',
                '--server.rest-server', 'false',
            ])
        # fmt: on
        self.progress(True, "step 5 restart the full cluster ")
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        for node in self.starter_instances:
            node.respawn_instance(version)
        self.progress(True, "step 6 wait for the cluster to be up")
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()

        # now the upgrade should be done.
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()
            node.probe_leader()
        self.set_frontend_instances()
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)

        if self.selenium:
            self.selenium.test_wait_for_upgrade()  # * 5s

    def downgrade_arangod_version_manual_impl(self):
        """manual upgrade this installation"""
        lh.subsubsection("wait for all shards to be in sync - downgrade")
        retval = self.starter_instances[0].arangosh.run_in_arangosh(
            (self.cfg.test_data_dir / Path("tests/js/server/cluster/wait_for_shards_in_sync.js")),
            [],
            ['true'],
        )
        if not retval:
            raise Exception(
                "Failed to ensure the cluster is in sync: %s" % (retval)
            )
        print("all in sync.")
        self.progress(True, "manual upgrade step 1 - stop instances")
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)
        for node in self.starter_instances:
            node.replace_binary_for_upgrade(self.new_installer.cfg, False)
        for node in self.starter_instances:
            node.detect_instance_pids_still_alive()

        # fmt: off
        self.progress(True, "step 2 - upgrade agents")
        for node in self.starter_instances:
            node.upgrade_instances(
                [
                    InstanceType.AGENT
                ], [
                    '--database.auto-upgrade', 'true',
                    '--log.foreground-tty', 'true'
                ],
                # mitigate 3.6x agency shutdown issues:
                self.cfg.version >= arangoversions['370'])
        self.progress(True, "step 3 - upgrade db-servers")
        for node in self.starter_instances:
            node.upgrade_instances([
                InstanceType.DBSERVER
            ], ['--database.auto-upgrade', 'true',
                '--log.foreground-tty', 'true'])
        self.progress(True, "step 4 - coordinator upgrade")
        # now the new cluster is running. we will now run the coordinator upgrades
        for node in self.starter_instances:
            logging.info("upgrading coordinator instances\n" + str(node))
            node.upgrade_instances([
                InstanceType.COORDINATOR
            ], [
                '--database.auto-upgrade', 'true',
                '--javascript.copy-installation', 'true',
                '--server.rest-server', 'false',
            ])
        # fmt: on
        self.progress(True, "step 5 restart the full cluster ")
        version = self.new_cfg.version if self.new_cfg is not None else self.cfg.version
        for node in self.starter_instances:
            node.respawn_instance(version)
        self.progress(True, "step 6 wait for the cluster to be up")
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()

        # now the upgrade should be done.
        for node in self.starter_instances:
            node.detect_instances()
            node.wait_for_version_reply()
            node.probe_leader()
        self.set_frontend_instances()
        self.starter_instances[0].maintainance(False, InstanceType.COORDINATOR)

        if self.selenium:
            self.selenium.test_wait_for_upgrade()  # * 5s

    @step
    def jam_attempt_impl(self):
        self.makedata_instances = self.starter_instances[:]
        logging.info("jamming: starting data stress")
        assert self.makedata_instances, "no makedata instance!"
        logging.debug("makedata instances")
        for i in self.makedata_instances:
            logging.debug(str(i))

        tcount = 0
        jobs = Queue()
        resultq = Queue()
        results = []
        workers = []
        no_dbs = self.scenario.db_count
        for i in range(self.scenario.db_count_chunks):
            jobs.put(
                {
                    "args": [
                        "TESTDB",
                        "--minReplicationFactor",
                        str(self.scenario.min_replication_factor),
                        "--maxReplicationFactor",
                        str(self.scenario.max_replication_factor),
                        "--dataMultiplier",
                        str(self.scenario.data_multiplier),
                        "--numberOfDBs",
                        str(no_dbs),
                        "--countOffset",
                        str((i + self.scenario.db_offset) * no_dbs + 1),
                        "--collectionMultiplier",
                        str(self.scenario.collection_multiplier),
                        "--singleShard",
                        "true" if self.scenario.single_shard else "false",
                    ]
                }
            )

        while len(workers) < self.scenario.parallelity:
            starter = self.makedata_instances[len(workers) % len(self.makedata_instances)]
            assert starter.arangosh, "no starter associated arangosh!"
            arangosh = starter.arangosh

            # must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                workers.append(
                    Thread(
                        target=makedata_runner,
                        args=(
                            jobs,
                            resultq,
                            arangosh,
                            self.scenario.progressive_timeout,
                        ),
                    )
                )

        thread_count = len(workers)
        for worker in workers:
            worker.start()
            time.sleep(self.scenario.launch_delay)

        while tcount < thread_count:
            res_line = resultq.get()
            if isinstance(res_line, bytes):
                results.append(str(res_line).split(","))
            else:
                tcount += 1

        for worker in workers:
            worker.join()
        ti.prompt_user(self.cfg, "DONE! press any key to shut down the SUT.")

    def shutdown_impl(self):
        for node in self.starter_instances:
            node.terminate_instance()
        logging.info("test ended")

    def before_backup_impl(self):
        
        pass

    def after_backup_impl(self):
        
        pass

    def set_selenium_instances(self):
        """set instances in selenium runner"""
        self.selenium.set_instances(
            self.cfg,
            self.starter_instances[0].arango_importer,
            self.starter_instances[0].arango_restore,
            [x for x in self.starter_instances[0].all_instances if x.instance_type == InstanceType.COORDINATOR][0],
            self.new_cfg,
        )

    def generate_keyfile(self, keyfile):
        """generate the ssl certificate file"""
        self.cert_op(
            [
                "tls",
                "keyfile",
                "--cacert=" + str(self.certificate_auth["cert"]),
                "--cakey=" + str(self.certificate_auth["key"]),
                "--keyfile=" + str(keyfile),
                "--host=" + self.cfg.publicip,
                "--host=localhost",
            ]
        )
