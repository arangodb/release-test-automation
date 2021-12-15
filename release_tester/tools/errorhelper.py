#!/usr/bin/env python3
""" user interactions """
# import sys


def prompt_to_continue(msg, interactive=True):
    """halt till the users tells to continue"""
    print("\n\n\n")
    print(msg)
    print("\n")
    if interactive:
        input("Press Enter to continue.")


def ask_continue(msg, interactive=True, default=False):
    """halt till feedback"""
    print(msg)
    if interactive:
        userinput = input("Continue y/n: ")
        if userinput in ["y", "Y"]:
            return True
        return False
    return default


def ask_continue_or_exit(msg, interactive=True, default=True, status=1):
    """ask the user whether to abort the execution or continue anyways"""
    if not ask_continue(msg, interactive, default):
        print()
        print("Abort requested (default action)")
        raise Exception("must not continue from here - bye " + str(status))
