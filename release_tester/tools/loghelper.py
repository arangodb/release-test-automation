#!/usr/bin/env python3
""" invoke subprocesses and timestamped print their output """
import subprocess

def get_term_width():
    """ eventually we should ask the term for the size """
    return 60

def line(sym="-", length=get_term_width()):
    """ adjust line to terminal width """
    print(sym * length)

def log_cmd(cmd):
    """ log string """
    if not isinstance(cmd, str):
        cmd = " ".join([str(x) for x in cmd])
    print()
    line("#")
    print("executing: " + str(cmd))
    line(">")

def LoggedCommandWait():
    """ run a command, redirect its output through our log facility, wait for its exit """
    def __init__(self, cmd_arr, *args, tool=subprocess.Popen, **kwargs):
        log_cmd(cmd_arr)
        self.child = tool(cmd_arr, *args, **kwargs)

    def __exit__(self):
        self.child.wait()
        line("<")
        print()


def subsection(name, sym="#", in_section=False):
    """ print a subsection """
    target_length = get_term_width()

    spaces = (target_length - len(name) - 2)
    spaces_front = int(spaces / 2)
    spaces_back = spaces - spaces_front

    if not in_section:
        print()
    line(sym, target_length)
    print(sym + " " * spaces_front + name + " " * spaces_back + sym)
    line(sym, target_length)

def section(name, sym="="):
    """ print a section """
    target_length = get_term_width()

    print()
    line(sym, target_length)
    subsection(name, sym, True)
    line(sym, target_length)
