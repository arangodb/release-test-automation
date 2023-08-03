#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging

# import os
from pathlib import Path
from queue import Queue
from threading import Thread

import psutil

from reporting.reporting_utils import step

# import statsd
import yaml

from arangodb.starter.deployments.runner import Runner, RunnerProperties
from arangodb.starter.deployments.cluster import Cluster

# from arangodb.starter.deployments.activefailover import ActiveFailover

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
        self.phase = "jam"
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
        self.bench_jobs = []
        self.arangosh_jobs = []
        self.system_makedata = False


# pylint: disable=global-variable-not-assigned
# statsdc = statsd.StatsClient("localhost", 8125)
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
            # statsdc.incr("completed")
            return False
    return True


def makedata_runner(queue, resq, arangosh, progressive_timeout):
    """operate one makedata instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print("starting my task! " + str(job["args"]))
            res = arangosh.create_test_data(
                "xx", args=job["args"], result_line_handler=result_line, progressive_timeout=progressive_timeout
            )
            if not res[0]:
                print("error executing test - giving up.")
                print(res[1])
                resq.put(1)
                break
            resq.put(res)
        except Exception as ex:
            print("No more work!" + str(ex))
            resq.put(-1)
            break


def arangosh_runner(queue, resq, arangosh, progressive_timeout):
    """operate one arangosh instance"""
    while True:
        try:
            # all tasks are already there. if done:
            job = queue.get(timeout=0.1)
            print("starting my arangosh task! " + str(job["args"]) + str(job["script"]))
            res = arangosh.run_script_monitored(
                [
                    "stress job",
                    arangosh.cfg.test_data_dir.resolve() / job["script"],
                ],
                args=job["args"],
                result_line_handler=result_line,
                progressive_timeout=progressive_timeout,
            )
            if not res[0]:
                print("error executing test - giving up.")
                print(res[1])
                resq.put(1)
                break
            resq.put(res)
        except Exception as ex:
            print("No more work!" + str(ex))
            resq.put(-1)
            break


# class ClusterPerf(Cluster):
class ClusterPerf(Cluster):
    # class ClusterPerf(ActiveFailover):
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
        replication2: bool,
        use_auto_certs: bool,
    ):
        global OTHER_SH_OUTPUT, RESULTS_TXT
        cfg = installer_set[0][1].cfg
        if not cfg.scenario.exists():
            cfg.scenario.write_text(yaml.dump(TestConfig()))
            raise Exception("have written %s with default config" % str(cfg.scenario))

        with open(cfg.scenario, encoding="utf8", mode="r") as fileh:
            self.scenario = yaml.load(fileh, Loader=yaml.Loader)
        # we want to skip Cluster.__init__
        # pylint: disable=non-parent-init-called
        Runner.__init__(
            self,
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("CLUSTER", 400, 600, self.scenario.hot_backup, ssl, replication2, use_auto_certs, 6),
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
        self.jobs = Queue()
        self.resultq = Queue()
        self.results = []
        self.makedata_workers = []
        self.arangosh_workers = []
        self.arangobench_workers = []
        self.arangosh_workers = []
        self.arangosh_instances = []
        self.no_dbs = self.scenario.db_count
        self.thread_count = 0
        self.tcount = 0
        # AFO
        # self.backup_instance_count = 1

        # pylint: disable=consider-using-with
        RESULTS_TXT = Path("/tmp/results.txt").open("w", encoding="utf8")
        OTHER_SH_OUTPUT = Path("/tmp/errors.txt").open("w", encoding="utf8")

    def _prolongue_backup_timeout(self):
        for starter in self.starter_instances:
            starter.hb_config.hb_timeout = 200000

    def _get_one_job(self, count):
        return {
            "args": [
                "TESTDB",
                "--minReplicationFactor",
                str(self.scenario.min_replication_factor),
                "--maxReplicationFactor",
                str(self.scenario.max_replication_factor),
                "--dataMultiplier",
                str(self.scenario.data_multiplier),
                "--numberOfDBs",
                str(self.no_dbs),
                "--countOffset",
                str((count + self.scenario.db_offset) * self.no_dbs + 1),
                "--collectionMultiplier",
                str(self.scenario.collection_multiplier),
                "--singleShard",
                "true" if self.scenario.single_shard else "false",
                "--progress",
                "true",
            ]
        }

    def _generate_makedata_jobs(self):
        """generate the workers instructions including offsets against overlapping"""
        for i in range(self.scenario.db_count_chunks):
            self.jobs.put(self._get_one_job(i))

    def _start_makedata_workers(self, frontends):
        """launch the worker threads"""
        # self.makedata_instances = self.starter_instances[:]
        assert self.makedata_instances, "no makedata instance!"
        logging.debug("makedata instances")
        for i in frontends:
            logging.debug(str(i))
        while len(frontends) < self.scenario.parallelity:
            starter = frontends[len(self.makedata_workers) % len(frontends)]
            assert starter.arangosh, "no starter associated arangosh!"
            arangosh = starter.arangosh

            # must be writabe that the setup may not have already data
            if not arangosh.read_only and not self.has_makedata_data:
                self.makedata_workers.append(
                    Thread(
                        target=makedata_runner,
                        args=(
                            self.jobs,
                            self.resultq,
                            arangosh,
                            self.scenario.progressive_timeout,
                        ),
                    )
                )
        self.thread_count = len(self.makedata_workers)
        for worker in self.makedata_workers:
            worker.start()
            time.sleep(self.scenario.launch_delay)

    def _start_arangosh_workers(self, frontends):
        """launch the worker threads"""
        # self.makedata_instances = self.starter_instances[:]
        assert self.makedata_instances, "no makedata instance!"
        print("arangosh instances")
        while len(self.arangosh_workers) < self.scenario.parallelity:
            starter = frontends[len(self.arangosh_workers) % len(frontends)]
            assert starter.arangosh, "no starter associated arangosh!"
            arangosh = starter.arangosh

            # must be writabe that the setup may not have already data
            if not arangosh.read_only:
                self.arangosh_workers.append(
                    Thread(
                        target=arangosh_runner,
                        args=(
                            self.jobs,
                            self.resultq,
                            arangosh,
                            self.scenario.progressive_timeout,
                        ),
                    )
                )
        self.thread_count = len(self.arangosh_workers)
        for worker in self.arangosh_workers:
            worker.start()
            time.sleep(self.scenario.launch_delay)

    def _kill_load_workers(self):
        """terminate them so it all ends quickly"""
        processes = psutil.process_iter()
        for process in processes:
            try:
                name = process.name()
                if name.startswith("arangosh"):
                    print(f"killing {process.name}  {process.pid}")
                    process.kill()
            except Exception as ex:
                logging.error(ex)
        for worker in self.arangobench_workers:
            worker.kill()

    def _shutdown_load_workers(self):
        """wait for the worker threads to be done"""
        for worker in self.makedata_workers:
            worker.join()
        for worker in self.arangosh_workers:
            worker.join()
        for worker in self.arangobench_workers:
            worker.wait()

    def starter_prepare_env_impl(self, sm=None):
        self.cfg.index = 0

        # pylint: disable=import-outside-toplevel
        if self.remote:
            from arangodb.starter.manager import StarterNonManager as StarterManager
        else:
            from arangodb.starter.manager import StarterManager

            super().starter_prepare_env_impl()
        # super().starter_prepare_env_impl(StarterManager)
        # += ['--agents.agency.election-timeout-min=5',
        #     '--agents.agency.election-timeout-max=10',]

    def make_data_impl(self):
        if self.scenario.system_makedata:
            super().make_data_impl()

    def check_data_impl_sh(self, arangosh, supports_foxx_tests):
        if self.scenario.system_makedata:
            super().check_data_impl_sh(arangosh, supports_foxx_tests)

    def check_data_impl(self):
        if self.scenario.system_makedata:
            super().check_data_impl()

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
        super().finish_setup_impl()
        # self.agency_set_debug_logging()
        # self.dbserver_set_debug_logging()
        # self.coordinator_set_debug_logging()

        # set_prometheus_jwt(self.starter_instances[0].get_jwt_header())

    def test_setup_impl(self):
        pass

    def after_makedata_check(self):
        pass

    # def wait_for_restore_impl(self, backup_starter):
    #    pass
    @step
    def jam_attempt_impl(self):
        if "jam" in self.scenario.phase:
            logging.info("jamming: starting data stress")
            self._generate_makedata_jobs()
            self._start_makedata_workers()

            while self.tcount < self.thread_count:
                res_line = self.resultq.get()
                if isinstance(res_line, bytes):
                    self.results.append(str(res_line).split(","))
                else:
                    self.tcount += 1
            self._shutdown_load_workers()

            ti.prompt_user(self.cfg, "DONE! press any key to shut down the SUT.")

    def before_backup_create_impl(self):
        self._prolongue_backup_timeout()
        count = 0
        frontends = self.get_frontend_starters()
        if "backup" in self.scenario.phase:
            logging.info("backup: starting data stress")
            count += 1
            self._generate_makedata_jobs(frontends)
            self._start_makedata_workers(frontends)
            # Let the test heat up before we continue with the backup:
            time.sleep(120)
        if "backuparangosh" in self.scenario.phase:
            for arangosh_job in self.scenario.arangosh_jobs:
                self.jobs.put(
                    {
                        "args": ["--count", str(count)],
                        # "--directory", self.
                        "script": arangosh_job,
                    }
                )
                count += 1
            self._start_arangosh_workers(frontends)

        if "backupbench" in self.scenario.phase:
            for bench_job in self.scenario.bench_jobs:
                self.arangobench_workers.append(frontends[count % len(frontends)].launch_arangobench(bench_job))
                time.sleep(0.1)
                count += 1
            time.sleep(0.5)
        time.sleep(count * 5)
        print(count)
        print("pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp")
        try:
            count = 0
            while count < 100:
                frontends[count % len(frontends)].hb_instance.create(f"ABC{count}")
                count += 1

            hb_job_params = self._get_one_job(9999)  # TODO calculate number

            starter = frontends[0]
            assert starter.arangosh, "no starter associated arangosh!"
            arangosh = starter.arangosh
            arangosh.create_test_data(
                "xx",
                args=hb_job_params["args"],
                result_line_handler=result_line,
                progressive_timeout=self.scenario.progressive_timeout,
            )
            frontends[count % len(frontends)].hb_instance.create(f"AFTER_LOAD")
            self._kill_load_workers()
            self._shutdown_load_workers()

            all_backups = self.list_backup()
            count = 0
            for one_backup in all_backups:
                if one_backup.find("AFTER_LOAD") >= 0:
                    print(one_backup)
                    self.upload_backup(one_backup)
                    self.delete_backup(one_backup)
                    print("Listing after locally deleting:")
                    self.list_backup()
                    self.download_backup(one_backup)
                    frontends[count % len(frontends)].hb_instance.restore(one_backup)
                    self.wait_for_restore_impl(frontends[count % len(frontends)])
                    frontends = self.get_frontend_starters()
                    starter = frontends[0]
                    assert starter.arangosh, "no starter associated arangosh!"
                    arangosh = starter.arangosh
                    arangosh.check_test_data(
                        "xx", supports_foxx_tests=True, args=hb_job_params["args"], result_line_handler=result_line
                    )
                count += 1
            count = 0
            for one_backup in all_backups:
                frontends[count % len(frontends)].hb_instance.restore(one_backup)
                self.wait_for_restore_impl(frontends[count % len(frontends)])
                frontends = self.get_frontend_starters()
                starter = frontends[0]
                assert starter.arangosh, "no starter associated arangosh!"
                arangosh = starter.arangosh
                count += 1
        except Exception as ex:
            print(ex)
            print("aborting test!")
            self._kill_load_workers()
            self._shutdown_load_workers()
            raise ex

    def after_backup_create_impl(self):
        if "backup" in self.scenario.phase:
            logging.info("backup: joining data stress")
            while self.tcount < self.thread_count:
                res_line = self.resultq.get()
                if isinstance(res_line, bytes):
                    self.results.append(str(res_line).split(","))
                else:
                    self.tcount += 1
            self._shutdown_load_workers()

            ti.prompt_user(self.cfg, "DONE! press any key to shut down the SUT.")
        if "backupbench" in self.scenario.phase:
            for bench_worker in self.arangobench_workers:
                bench_worker.kill()
                bench_worker.wait()
