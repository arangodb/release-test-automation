#!/usr/bin/env python3
import subprocess

def get_term_width():
    # eventually we should ask the term for the size
    return 60

def line(sym = "-", length = get_term_width()):
    print(sym * length)

def log_cmd(cmd):
    if not isinstance(cmd,str):
        cmd = " ".join([str(x) for x in cmd])
    print()
    line("#")
    print("executing: " + str(cmd))
    line(">")

def LoggedCommandWait():
    def __init__(self,  cmd_arr ,*args, tool = subprocess.Popen, **kwargs):
        log.cmd(cmd_arr)
        self.child = tool(cmd_arr ,*args, **kwargs)

    def __exit__(self):
        self.child.wait()
        line("<")
        print()


def subsection(name, sym="#", in_section=False):
    target_length = get_term_width()

    spaces = (target_length - len(name) - 2)
    spaces_front = int(spaces / 2)
    spaces_back = spaces - spaces_front

    if not in_section: print()
    line(sym, target_length)
    print(sym + " " * spaces_front + name + " " * spaces_back + sym)
    line(sym, target_length)

def section(name, sym="="):
    target_length = get_term_width()

    print()
    line(sym, target_length)
    subsection(name, sym, True)
    line(sym, target_length)
