""" running CLI programs in subprocesses """
import logging

# pylint: disable=logging-fstring-interpolation
from reporting.reporting_utils import step

from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    make_default_params
)

class RunAnonProgramm(ArangoCLIprogressiveTimeoutExecutor):
    """manage any program"""
    def __init__(self,  cfg):
        super().__init__(cfg, None)

@step
def run_cmd_and_log_stdout_async(cfg, cmd, timeout=1200):
    """run command and save output"""
    logging.info(f"Running command:\n{cmd}")
    prog = RunAnonProgramm(cfg)
    params = make_default_params(cfg.verbose)
    return prog.run_monitored(cmd[0], cmd[1:], params, timeout)
