#!/usr/bin/env python3
import sys

def prompt_to_continue(interactive=True):
    if interative:
        input("Press Enter to continue.")

def ask_continue(interactive=True, defualt=True):
    if interative:
        x = input("Continue y/n:")
        if x in ['y', 'Y']:
            return True
        return False
    else:
        return default

def ask_continue_or_exit(interactive=True, default=True, status=1):
    if not ask_continue(interactive, default):
        sys.exit(status)
