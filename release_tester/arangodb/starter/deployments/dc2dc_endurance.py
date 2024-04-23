#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time

from arangodb.starter.deployments.dc2dc import Dc2Dc


class Dc2DcEndurance(Dc2Dc):
    """this launches two clusters in dc2dc mode"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-function-args
    def __init__(
        self,
        runner_type,
        abort_on_error,
        installer_set,
        selenium,
        selenium_driver_args,
        selenium_include_suites,
        testrun_name: str,
        ssl: bool,
        replication2: bool,
        use_auto_certs: bool,
        force_one_shard: bool,
        create_oneshard_db: bool,
        cluster_nodes: int,
    ):
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            selenium,
            selenium_driver_args,
            selenium_include_suites,
            testrun_name,
            ssl,
            replication2,
            use_auto_certs,
            force_one_shard,
            create_oneshard_db,
            cluster_nodes,
        )
        self.hot_backup = False

    def test_setup_impl(self):
        scenarios = ["A", "B", "C", "D", "E", "G", "H"]
        bench_instances = []
        for scenario in scenarios:
            time.sleep(5)
            bench_instances.append(
                self.cluster1["instance"].launch_arangobench("dc2dc_" + scenario, ["--duration", "60"])
            )
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        for instance in bench_instances:
            if not instance.wait():
                print(instance.arguments)
            else:
                print("SUCCESSS!")

        self.sync_manager.check_sync()

    def before_backup_impl(self):
        self.sync_manager.stop_sync()

    def after_backup_impl(self):
        count = 0
        while not self.sync_manager.check_sync():
            if count > 20:
                raise Exception("failed to get the sync status")
            time.sleep(10)
            count += 1
