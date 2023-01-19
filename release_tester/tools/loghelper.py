#!/usr/bin/env python3
""" invoke subprocesses and timestamped print their output """
# pylint: disable=no-member,no-name-in-module
import logging
from logging import StreamHandler, Handler
import sys

from allure_commons._allure import attach
from allure_commons.types import AttachmentType


class StdOutHandler(StreamHandler):
    """stdout handler adapter"""
    # pylint: disable=super-init-not-called disable=non-parent-init-called
    def __init__(self):
        Handler.__init__(self)

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            sys.stdout.flush()
        finally:
            self.release()

    def emit(self, record):
        # pylint: disable=broad-except
        try:
            msg = self.format(record)
            stream = sys.stdout
            stream.write(msg + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)

    def __repr__(self):
        level = logging.getLevelName(self.level)
        return "<%s (%s)>" % (self.__class__.__name__, level)


def configure_logging(verbose):
    """set up logging"""
    logging.basicConfig(
        # level=logging.DEBUG,
        datefmt="%H:%M:%S",
        format="%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s",
    )
    logging.basicConfig()
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.info("setting debug level to INFO")
        logging.getLogger().setLevel(logging.INFO)

    loggers = [
        ["urllib3", logging.WARNING, True],
        ["requests", logging.WARNING, True],
        ["selenium.webdriver.remote.remote_connection", logging.WARNING, True],
        ["MARKDOWN", logging.WARNING, True],
    ]

    for one_logger in loggers:
        logger = logging.getLogger(one_logger[0])
        logger.setLevel(one_logger[1])
        logger.propagate = one_logger[2]

    logger = logging.getLogger()
    for handler in logger.handlers:
        logger.removeHandler(handler)
    handler = StdOutHandler()
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_term_width():
    """eventually we should ask the term for the size"""
    return 60


def line(sym="-", length=get_term_width()):
    """adjust line to terminal width"""
    print(sym * int(length / len(sym)))


def log_cmd(cmd, print_cmd=True):
    """log string"""
    if not isinstance(cmd, str):
        cmd = str(" ".join([str(x) for x in cmd]))
    attach(cmd, "Command", attachment_type=AttachmentType.TEXT)
    if print_cmd:
        line("<")
        print("executing: " + cmd)
        line("^")


# def logged_command_wait():
#     """ run a command, redirect its output
#         through our log facility, wait for its exit """
#     def __init__(self, cmd_arr, *args, tool=subprocess.Popen, **kwargs):
#         log_cmd(cmd_arr)
#         self.child = tool(cmd_arr, *args, **kwargs)
#
#     def __exit__(self):
#         self.child.wait()
#         line("<")
#         print()


def subsection(name, sym="=", in_section=False):
    """print a subsection"""
    target_length = get_term_width()

    spaces = target_length - len(name) - 2 * len(sym)
    spaces_front = int(spaces / 2)
    spaces_back = spaces - spaces_front

    if not in_section:
        print()
    line(sym, target_length)
    print(sym + " " * spaces_front + name + " " * spaces_back + sym)
    line(sym, target_length)


def subsubsection(name, sym="-"):
    """print a subsubsection"""
    subsection(name, sym, False)


def section(name, sym="#"):
    """print a section"""
    target_length = get_term_width()

    print()
    line(sym, target_length)
    subsection(name, sym, True)
    line(sym, target_length)
