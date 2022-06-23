""" running CLI programs in subprocesses """
import sys
import logging
from subprocess import PIPE

import psutil


# pylint: disable=logging-fstring-interpolation
def run_cmd_and_log_stdout(cmd, timeout=1200):
    """run and collect the output of cmd"""
    if type(cmd) == list:
        cmd_str = " ".join(cmd)
    else:
        cmd_str = cmd
    run = psutil.Popen(cmd, stdout=PIPE, stderr=PIPE)
    logging.info(f"running command:\n{cmd_str}\nwith PID: {run.pid}")
    try:
        run.wait(timeout)
    except psutil.TimeoutExpired as exc:
        raise Exception(f"ERROR: Process could not complete in set timeout of {timeout} seconds.") from exc
    finally:
        sys.stdout.write(run.stdout.read().decode())
        sys.stderr.write(run.stderr.read().decode())
    return run.pid
