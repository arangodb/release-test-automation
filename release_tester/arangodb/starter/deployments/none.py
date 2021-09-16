
#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""

from arangodb.starter.deployments.runner import Runner, RunnerProperties

class NoStarter(Runner):
    """ This runner does not use the starter """
# pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, abort_on_error, installer_set,
                 selenium, selenium_driver_args,
                 testrun_name: str,
                 ssl: bool,
                 use_auto_certs: bool):
        super().__init__(runner_type, abort_on_error, installer_set,
                         RunnerProperties('none', 0, 0, False, ssl, use_auto_certs),
                         selenium, selenium_driver_args,
                         testrun_name)

    def starter_prepare_env_impl(self):
        """ nothing to see here """

    def starter_run_impl(self):
        """ nothing to see here """

    def finish_setup_impl(self):
        """ nothing to see here """

    def test_setup_impl(self):
        """ nothing to see here """

    def upgrade_arangod_version_impl(self):
        """ nothing to see here """

    def upgrade_arangod_version_manual_impl(self):
        """ nothing to see here """

    def jam_attempt_impl(self):
        """ nothing to see here """

    def shutdown_impl(self):
        """ nothing to see here """

    def before_backup_impl(self):
        """ nothing to see here """

    def after_backup_impl(self):
        """ nothing to see here """
