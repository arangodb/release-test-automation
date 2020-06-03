
#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""

from arangodb.starter.deployments.runner import Runner

class NoStarter(Runner):
    """ This runner does not use the starter """
    def __init__(self, runner_type, cfg, new_inst, old_inst):
        super().__init__(runner_type, cfg, new_inst, old_inst, 'none')

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
