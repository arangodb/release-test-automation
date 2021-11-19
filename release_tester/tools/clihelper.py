""" running CLI programs in subprocesses """
import sys
import logging
import psutil


def run_cmd_and_log_stdout(cmd):
    run = psutil.Popen(cmd)
    logging.info(f"running command:\n{cmd}\nwith PID: {run.pid}")
    run.wait()
    sys.stdout.write(run.stdout.read().decode())
    sys.stderr.write(run.stderr.read().decode())
    return run.pid