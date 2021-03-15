#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time

from arangodb.starter.deployments.dc2dc import Dc2Dc

class Dc2DcEndurance(Dc2Dc):
    """ this launches two clusters in dc2dc mode """
    # pylint: disable=R0913 disable=R0902
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst,
                 selenium, selenium_driver_args):
        super().__init__(runner_type, cfg, old_inst, new_cfg, new_inst,
                         'DC2DC_endurance', 0, 3500, selenium, selenium_driver_args)
        self.hot_backup = False

    def test_setup_impl(self):
        scenarios = ['A', 'B', 'C', 'D', 'E', 'G', 'H']
        bench_instances = []
        for scenario in scenarios:
            time.sleep(5)
            bench_instances.append(
                self.cluster1['instance'].launch_arangobench(
                    'dc2dc_'+scenario,
                    ['--duration', '60'])
            )
        self.sync_manager.check_sync_status(0)
        self.sync_manager.check_sync_status(1)
        for instance in bench_instances:
            if not instance.wait():
                print(instance.arguments)
            else:
                print("SUCCESSS!")

        self.sync_manager.check_sync()
