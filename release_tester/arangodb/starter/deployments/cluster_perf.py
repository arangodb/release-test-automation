#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
# import os
from pathlib import Path
from queue import Queue, Empty
from threading import Thread

from reporting.reporting_utils import step
# import statsd
import yaml

from arangodb.starter.deployments.runner import Runner, RunnerProperties
from arangodb.starter.deployments.cluster import Cluster

# from tools.asciiprint import print_progress as progress
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

# pylint: disable=unused-argument
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


class ClusterPerf(Cluster):
    """this launches a cluster setup"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
    # pylint: disable=super-init-not-called
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
        # we want to skip Cluster.__init__
        # pylint: disable=non-parent-init-called
        Runner.__init__(
            self,
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
        # pylint: disable=consider-using-with
        RESULTS_TXT = Path("/tmp/results.txt").open("w", encoding='utf8')
        OTHER_SH_OUTPUT = Path("/tmp/errors.txt").open("w", encoding='utf8')

    def starter_prepare_env_impl(self, sm=None):
        self.cfg.index = 0

        # pylint: disable=import-outside-toplevel
        if self.remote:
            from arangodb.starter.manager import StarterNonManager as StarterManager
        else:
            from arangodb.starter.manager import StarterManager
        super().starter_prepare_env_impl(StarterManager)
         # += ['--agents.agency.election-timeout-min=5',
         #     '--agents.agency.election-timeout-max=10',]

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
        super().starter_run_impl()

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

    def wait_for_restore_impl(self, backup_starter):
        pass
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

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
