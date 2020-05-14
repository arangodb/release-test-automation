#!/usr/bin/env python3
import subprocess

def get_term_width():
    # eventually we should ask the term for the size
    return 60

def line(sym = "-", length = get_term_width()):
    print(sym * length)

def log_cmd(cmd):
    line(">")
    if not isinstance(cmd,str):
        cmd = " ".join([str(x) for x in cmd])
    print("executing: " + str(cmd))

def LoggedCommandWait():
    def __init__(self, cmd_arr ,*args, **kwargs):
        log.cmd(cmd_arr)
        self.child = subprocess.Popen(cmd_arr ,*args, **kwargs)

    def __exit__(self):
        self.child.wait()
        line("<")


def section(name):
    target_length = get_term_width()
    spaces = (target_length - len(name) - 2)
    spaces_front = int(spaces / 2)
    spaces_back = spaces - spaces_front

    line("x", target_length)
    print("x" + " " * spaces_front + name + " " * spaces_back + "x")
    line("x", target_length)
