
#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""

from arangodb.starter.deployments.runner import Runner

class NoStarter(Runner):
    """ This runner does not use the starter """
# pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst,
                 selenium, selenium_driver_args):
        super().__init__(runner_type, cfg,
                         old_inst, new_cfg, new_inst,
                         'none', 0, 0, selenium, selenium_driver_args)

    def starter_prepare_env_impl(self):
        pass

    def starter_run_impl(self):
        pass

    def finish_setup_impl(self):
        pass

    def test_setup_impl(self):
        pass

    def upgrade_arangod_version_impl(self):
        pass

    def jam_attempt_impl(self):
        pass

    def shutdown_impl(self):
        pass

    def before_backup_impl(self):
        pass

    def after_backup_impl(self):
        pass
