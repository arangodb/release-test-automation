#!/usr/bin/env python
""" launch and manage an arango deployment using the starter"""
import time
import logging
from pathlib import Path

import psutil
import requests
from arangodb.starter.manager import StarterManager
from arangodb.sync import SyncManager
from arangodb.instance import InstanceType
from arangodb.starter.deployments.dc2dc import Dc2Dc

class Dc2DcEndurance(Dc2Dc):
    """ this launches two clusters in dc2dc mode """
    def __init__(self, runner_type, cfg, old_inst, new_cfg, new_inst):
        super(Dc2Dc, self).__init__(runner_type, cfg, old_inst, new_cfg, new_inst, 'DCendurance', 0, 4000)
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
