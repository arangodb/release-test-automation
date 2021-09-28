#!/usr/bin/env python3
""" invoke subprocesses and timestamped print their output """
# import subprocess
import logging

from allure_commons._allure import attach

def configure_logging(verbose):
    """ set up logging """
    logging.basicConfig(
        # level=logging.DEBUG,
        datefmt='%H:%M:%S',
        format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
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
        ["MARKDOWN", logging.WARNING, True]
    ]

    for l in loggers:
        logger = logging.getLogger(l[0])
        logger.setLevel(l[1])
        logger.propagate = l[2]

def get_term_width():
    """ eventually we should ask the term for the size """
    return 60


def line(sym="-", length=get_term_width()):
    """ adjust line to terminal width """
    print(sym * int (length / len(sym)))


def log_cmd(cmd, print_cmd=True):
    """ log string """
    if not isinstance(cmd, str):
        cmd = str(" ".join([str(x) for x in cmd]))
    attach(cmd, "Command")
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
    """ print a subsection """
    target_length = get_term_width()

    spaces = (target_length - len(name) - 2 * len(sym))
    spaces_front = int(spaces / 2)
    spaces_back = spaces - spaces_front

    if not in_section:
        print()
    line(sym, target_length)
    print(sym + " " * spaces_front + name + " " * spaces_back + sym)
    line(sym, target_length)

def subsubsection(name, sym="-"):
    """ print a subsubsection """
    subsection(name, sym, False)

def section(name, sym="#"):
    """ print a section """
    target_length = get_term_width()

    print()
    line(sym, target_length)
    subsection(name, sym, True)
    line(sym, target_length)
