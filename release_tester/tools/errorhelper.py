#!/usr/bin/env python3
import sys

def prompt_to_continue(msg, interactive=True):
    print("\n\n\n")
    print(msg)
    print("\n")
    if interactive:
        input("Press Enter to continue.")

def ask_continue(msg, interactive=True, default=False):
    print(msg)
    if interactive:
        x = input("Continue y/n: ")
        if x in ['y', 'Y']:
            return True
        return False
    else:
        return default

def ask_continue_or_exit(msg, interactive=True, default=True, status=1):
    if not ask_continue(msg, interactive, default):
        print()
        print("Abort requested (default action)")
        sys.exit(status)
