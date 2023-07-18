#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """

import os
from copy import deepcopy
from queue import Queue, Empty
import platform
import signal
import sys
from datetime import datetime, timedelta
from subprocess import PIPE
from threading import Thread
import psutil
from allure_commons._allure import attach
import tools.loghelper as lh

from tools.asciiprint import print_progress as progress

# import tools.loghelper as lh

ON_POSIX = "posix" in sys.builtin_module_names
IS_WINDOWS = platform.win32_ver()[0] != ""


def print_log(string, params):
    """only print if thread debug logging is enabled"""
    if params["trace_io"]:
        print(string)


def default_line_result(wait, line, params):
    """
    Keep the line, filter it for leading #,
    if verbose print the line. else print progress.
    """
    # pylint: disable=pointless-statement
    if params["verbose"] and wait > 0 and line is None:
        progress("sj" + str(wait))
        return True
    if isinstance(line, tuple):
        if params["verbose"]:
            print("e: " + str(line[0], "utf-8").rstrip())
        if not str(line[0]).startswith("#"):
            params["output"].append(line[0])
        else:
            return False
    return True


def make_default_params(verbose):
    """create the structure to work with arrays to output the strings to"""
    return {"trace_io": False, "error": "", "verbose": verbose, "output": [], "identifier": ""}


def make_logfile_params(verbose, logfile, trace):
    """create the structure to work with logfiles"""
    return {
        "trace_io": True,
        "trace": trace,
        "error": "",
        "verbose": verbose,
        "output": logfile.open("wb"),
        "identifier": "",
        "lfn": str(logfile),
    }


def logfile_line_result(wait, line, params):
    """Write the line to a logfile, print progress."""
    # pylint: disable=pointless-statement
    if params["trace"] and wait > 0 and line is None:
        progress("sj" + str(wait))
        return True
    if isinstance(line, tuple):
        if params["trace"]:
            print("e: " + str(line[0], "utf-8").rstrip())
        params["output"].write(line[0])
    return True


def delete_logfile_params(params):
    """teardown the structure to work with logfiles"""
    print(f"{params['identifier']} closing {params['lfn']}")
    params["output"].flush()
    params["output"].close()
    print(f"{params['identifier']} {params['lfn']} closed")


def enqueue_stdout(std_out, queue, instance, identifier, params):
    """add stdout to the specified queue"""
    try:
        for line in iter(std_out.readline, b""):
            # print("O: " + str(line))
            queue.put((line, instance))
    except ValueError as ex:
        print_log(f"{identifier} communication line seems to be closed: {str(ex)}", params)
    print_log(f"{identifier} x0 done!", params)
    queue.put(-1)
    std_out.close()


def enqueue_stderr(std_err, queue, instance, identifier, params):
    """add stderr to the specified queue"""
    try:
        for line in iter(std_err.readline, b""):
            # print("E: " + str(line))
            queue.put((line, instance))
    except ValueError as ex:
        print_log(f"{identifier} communication line seems to be closed: {str(ex)}", params)
    print_log(f"{identifier} x1 done!", params)
    queue.put(-1)
    std_err.close()


def convert_result(result_array):
    """binary -> string"""
    result = ""
    for one_line in result_array:
        if isinstance(one_line, str):
            result += "\n" + one_line.rstrip()
        else:
            result += "\n" + one_line.decode("utf-8").rstrip()
    return result


def add_message_to_report(params, string):
    """add a message from python to the report strings/files + print it"""
    print(string)
    if isinstance(params["output"], list):
        params["output"] += f"{'v'*80}\n{datetime.now()}>>>{string}<<<\n{'^'*80}\n"
    else:
        params["output"].write(bytearray(f"{'v'*80}\n{datetime.now()}>>>{string}<<<\n{'^'*80}\n", "utf-8"))
        params["output"].flush()
    sys.stdout.flush()
    return string + "\n"


def kill_children(identifier, params, children):
    """slash all processes enlisted in children - if they still exist"""
    err = ""
    killed = []
    for one_child in children:
        if one_child.pid in killed:
            continue
        try:
            killed.append(one_child.pid)
            err += add_message_to_report(params, f"{identifier}: killing {one_child.name()} - {str(one_child.pid)}")
            one_child.resume()
        except FileNotFoundError:
            pass
        except AttributeError:
            pass
        except ProcessLookupError:
            pass
        except psutil.NoSuchProcess:
            pass
        except psutil.AccessDenied:
            pass
        try:
            one_child.kill()
        except psutil.NoSuchProcess:  # pragma: no cover
            pass
    print_log(f"{identifier}: Waiting for the children to terminate", params)
    psutil.wait_procs(children, timeout=20)
    return err


class CliExecutionException(Exception):
    """transport CLI error texts"""

    def __init__(self, message, execution_result, have_timeout):
        super().__init__()
        self.execution_result = execution_result
        self.message = message
        self.have_timeout = have_timeout


def expect_failure(expect_to_fail, ret, params):
    """convert results, throw error if wanted"""
    attach(str(ret["rc_exit"]), f"Exit code: {str(ret['rc_exit'])} == {expect_to_fail}")
    res = (None, None, None, None)
    if ret["have_deadline"] or ret["progressive_timeout"]:
        res = (False, convert_result(params["output"]), 0, ret["line_filter"])
        raise CliExecutionException("Execution failed.", res, ret["progressive_timeout"] or ret["have_deadline"])
    if ret["rc_exit"] != 0:
        res = (False, convert_result(params["output"]), 0, ret["line_filter"])
        if expect_to_fail:
            return res
        raise CliExecutionException("Execution failed.", res, False)

    if not expect_to_fail:
        if len(params["output"]) == 0:
            res = (True, "", 0, ret["line_filter"])
        else:
            res = (True, convert_result(params["output"]), 0, ret["line_filter"])
        return res

    if len(params["output"]) == 0:
        res = (True, "", 0, ret["line_filter"], params["error"])
    else:
        res = (True, convert_result(params["output"]), 0, ret["line_filter"])
    raise CliExecutionException(
        f"{params.identifier} Execution was expected to fail, but exited successfully.", res, ret["progressive_timeout"]
    )


ID_COUNTER = 0


class ArangoCLIprogressiveTimeoutExecutor:
    """
    Abstract base class to run arangodb cli tools
    with username/password/endpoint specification
    timeout will be relative to the last thing printed.
    """

    # pylint: disable=too-few-public-methods too-many-arguments disable=too-many-instance-attributes disable=too-many-statements disable=too-many-branches disable=too-many-locals
    def __init__(self, config, connect_instance, deadline_signal=-1):
        """launcher class for cli tools"""
        self.connect_instance = connect_instance
        # if we don't copy the config, it causes chain upgrade tests to fail,
        # because passvoid attribute gets wiped somehow
        self.cfg = deepcopy(config)
        self.old_version = config.version
        self.deadline_signal = deadline_signal
        if self.deadline_signal == -1:
            # pylint: disable=no-member
            # yes, one is only there on the wintendo, the other one elsewhere.
            if IS_WINDOWS:
                self.deadline_signal = signal.CTRL_BREAK_EVENT
            else:
                self.deadline_signal = signal.SIGINT

    def __repr__(self):
        return """{0.__class__.__name__}
cfg: {0.cfg}
connect_instance: {0.connect_instance}
deadline_signal: {0.deadline_signal}""".format(
            self
        )

    def run_arango_tool_monitored(
        self,
        executeable,
        more_args,
        use_default_auth=True,
        params=None,
        progressive_timeout=60,
        deadline=0,
        deadline_grace_period=180,
        result_line_handler=default_line_result,
        expect_to_fail=False,
        identifier="",
    ):
        """
        runs a script in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        if params is None:
            params = {"error": "", "verbose": True, "output": []}
        # fmt: off
        passvoid = ''
        if self.cfg.passvoid:
            passvoid  = str(self.cfg.passvoid)
        elif self.connect_instance:
            passvoid = str(self.connect_instance.get_passvoid())
        if passvoid is None:
            passvoid = ''

        run_cmd = [
            "--log.foreground-tty", "true",
            "--log.force-direct", "true",
        ]
        if self.connect_instance:
            run_cmd += ["--server.endpoint", self.connect_instance.get_endpoint()]
            if use_default_auth:
                run_cmd += ["--server.username", str(self.cfg.username)]
                run_cmd += ["--server.password", passvoid]

        run_cmd += more_args
        ret = self.run_monitored(executeable,
                                 run_cmd,
                                 params,
                                 progressive_timeout,
                                 deadline,
                                 deadline_grace_period,
                                 result_line_handler,
                                 identifier)
        return expect_failure(expect_to_fail, ret, params)

    # fmt: on
    def run_monitored(
        self,
        executeable,
        args,
        params=None,
        progressive_timeout=60,
        deadline=0,
        deadline_grace_period=180,
        result_line_handler=default_line_result,
        identifier="",
    ):
        """
        run a script in background tracing with a dynamic timeout that its got output
        Deadline will represent an absolute timeout at which it will be signalled to
        exit, and yet another minute later a hard kill including sub processes will
        follow.
        (is still alive...)
        """
        if params is None:
            params = {"error": "", "verbose": True, "output": []}
        rc_exit = None
        line_filter = False
        run_cmd = [executeable] + args
        children = []
        if identifier == "":
            # pylint: disable=global-statement
            global ID_COUNTER
            my_no = ID_COUNTER
            ID_COUNTER += 1
            identifier = f"IO_{str(my_no)}"
        print(params)
        params["identifier"] = identifier
        if not isinstance(deadline, datetime):
            if deadline == 0:
                deadline = datetime.now() + timedelta(seconds=progressive_timeout * 10)
            else:
                deadline = datetime.now() + timedelta(seconds=deadline)
        final_deadline = deadline + timedelta(seconds=deadline_grace_period)
        lh.log_cmd(run_cmd)
        with psutil.Popen(
            run_cmd,
            stdout=PIPE,
            stderr=PIPE,
            close_fds=ON_POSIX,
            cwd=self.cfg.test_data_dir.resolve(),
        ) as process:
            queue = Queue()
            thread1 = Thread(
                name=f"readIO {identifier}",
                target=enqueue_stdout,
                args=(process.stdout, queue, self.connect_instance, identifier, params),
            )
            thread2 = Thread(
                name="readErrIO {identifier}",
                target=enqueue_stderr,
                args=(process.stderr, queue, self.connect_instance, identifier, params),
            )
            thread1.start()
            thread2.start()

            try:
                print(
                    "{0} me PID:{1} launched PID:{2} with LWPID:{3} and LWPID:{4}".format(
                        identifier, str(os.getpid()), str(process.pid), str(thread1.native_id), str(thread2.native_id)
                    )
                )
            except AttributeError:
                print(
                    "{0} me PID:{1} launched PID:{2} with LWPID:N/A and LWPID:N/A".format(
                        identifier, str(os.getpid()), str(process.pid)
                    )
                )

            # read line without blocking
            have_progressive_timeout = False
            tcount = 0
            close_count = 0
            have_deadline = 0
            deadline_grace_count = 0
            while not have_progressive_timeout:
                # if you want to tail the output, enable this:
                # out.flush()
                result_line_handler(tcount, None, params)
                line = ""
                try:
                    line = queue.get(timeout=1)
                    ret = result_line_handler(0, line, params)
                    line_filter = line_filter or ret
                    tcount = 0
                    if not isinstance(line, tuple):
                        close_count += 1
                        print_log(f"{identifier} 1 IO Thead done!", params)
                        if close_count == 2:
                            break
                except Empty:
                    tcount += 1
                    have_progressive_timeout = tcount >= progressive_timeout
                    if have_progressive_timeout:
                        try:
                            children = process.children(recursive=True)
                        except psutil.NoSuchProcess:
                            pass
                        process.kill()
                        kill_children(identifier, params, children)
                        rc_exit = process.wait()
                if datetime.now() > deadline:
                    have_deadline += 1
                if have_deadline == 1:
                    add_message_to_report(
                        params, f"{identifier} Execution Deadline reached - will trigger signal {self.deadline_signal}!"
                    )
                    # Send the process our break / sigint
                    try:
                        children = process.children(recursive=True)
                    except psutil.NoSuchProcess:
                        pass
                    process.send_signal(self.deadline_signal)
                elif have_deadline > 1 and datetime.now() > final_deadline:
                    try:
                        # give it some time to exit:
                        print_log(f"{identifier} try wait exit:", params)
                        try:
                            children = children + process.children(recursive=True)
                        except psutil.NoSuchProcess:
                            pass
                        rc_exit = process.wait(1)
                        add_message_to_report(params, f"{identifier}  exited: {str(rc_exit)}")
                        kill_children(identifier, params, children)
                        print_log(f"{identifier}  closing", params)
                        process.stderr.close()
                        process.stdout.close()
                        break
                    except psutil.TimeoutExpired:
                        deadline_grace_count += 1
                        print_log(f"{identifier} timeout waiting for exit {str(deadline_grace_count)}", params)
                        # if its not willing, use force:
                        if deadline_grace_count > deadline_grace_period:
                            print_log(f"{identifier} getting children", params)
                            try:
                                children = process.children(recursive=True)
                            except psutil.NoSuchProcess:
                                pass
                            kill_children(identifier, params, children)
                            add_message_to_report(params, f"{identifier} killing")
                            process.kill()
                            print_log(f"{identifier} waiting", params)
                            rc_exit = process.wait()
                            print_log(f"{identifier} closing", params)
                            process.stderr.close()
                            process.stdout.close()
                            break
            print_log(f"{identifier} IO-Loop done", params)
            timeout_str = ""
            if have_progressive_timeout:
                timeout_str = "TIMEOUT OCCURED!"
                print(timeout_str)
                timeout_str += "\n"
            elif rc_exit is None:
                print_log(f"{identifier} waiting for regular exit", params)
                rc_exit = process.wait()
                print_log(f"{identifier} done", params)
            kill_children(identifier, params, children)
            print_log(f"{identifier} joining io Threads", params)
            thread1.join()
            thread2.join()
            print_log(f"{identifier} OK", params)

        return {
            "progressive_timeout": have_progressive_timeout,
            "have_deadline": have_deadline,
            "rc_exit": rc_exit,
            "line_filter": line_filter,
        }
