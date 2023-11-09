""" running CLI programs in subprocesses """
import sys
import logging
from subprocess import PIPE

import psutil


# pylint: disable=logging-fstring-interpolation
from reporting.reporting_utils import step


from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    make_default_params,
    convert_result,
    expect_failure,
    CliExecutionException,
)

class RunAnonProgramm(ArangoCLIprogressiveTimeoutExecutor):
    """manage any program"""
    def __init__(self,  cfg):
        super().__init__(cfg, None)

@step
def run_cmd_and_log_stdout(cmd, timeout=1200):
    """run command and save output"""
    logging.info(f"Running command:\n{cmd}")
    run = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
    logging.info(f"Command started with PID: {run.pid}")
    try:
        run.wait(timeout)
    except psutil.TimeoutExpired as exc:
        raise Exception(f"ERROR: Process could not complete in set timeout of {timeout} seconds.") from exc
    finally:
        sys.stdout.write(run.stdout.read().decode())
        sys.stderr.write(run.stderr.read().decode())
    return run.pid

@step
def run_cmd_and_log_stdout_asnyc(cfg, cmd, timeout=1200):
    """run command and save output"""
    logging.info(f"Running command:\n{cmd}")
    prog = RunAnonProgramm(cfg)
    params = make_default_params(cfg.verbose)
    return prog.run_monitored(cmd[0], cmd[1:], params, timeout)
