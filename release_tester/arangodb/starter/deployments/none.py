#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""

from arangodb.starter.deployments.runner import Runner, RunnerProperties


class NoStarter(Runner):
    """This runner does not use the starter"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes
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
        one_shard: bool,
        cluster_nodes: int,
    ):
        self.msg = ""
        super().__init__(
            runner_type,
            abort_on_error,
            installer_set,
            RunnerProperties("none", 0, 1, False, ssl, replication2, use_auto_certs, one_shard, 1),
            selenium,
            selenium_driver_args,
            selenium_include_suites,
            testrun_name,
        )

    def starter_prepare_env_impl(self):
        """nothing to see here"""

    def starter_run_impl(self):
        """nothing to see here"""

    def finish_setup_impl(self):
        """nothing to see here"""

    def test_setup_impl(self):
        """nothing to see here"""

    def upgrade_arangod_version_impl(self):
        """nothing to see here"""

    def upgrade_arangod_version_manual_impl(self):
        """nothing to see here"""

    def jam_attempt_impl(self):
        """nothing to see here"""

    def shutdown_impl(self):
        """nothing to see here"""

    def before_backup_impl(self):
        """nothing to see here"""

    def before_backup_create_impl(self):
        """nothing to see here"""

    def after_backup_create_impl(self):
        """HotBackup has happened, prepare the SUT to continue testing"""

    def after_backup_impl(self):
        """nothing to see here"""
