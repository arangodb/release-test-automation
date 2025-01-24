#!/usr/bin/env python
""" check whether the linux host has properly configured locales """
import os
import re
import sys


def detect_locale():
    """check that system locale is set correctly"""
    if sys.platform != "linux":
        return

    locale_env = {
        "LANG": r"en_US(|:.*)",
        "LANGUAGE": r"en_US(|:.*)",
        "LC_CTYPE": r"(^$)|(en_US(|:.*))",
        "LC_NUMERIC": r"(^$)|(en_US(|:.*))",
        "LC_TIME": r"(^$)|(en_US(|:.*))",
        "LC_COLLATE": r"(^$)|(en_US(|:.*))",
        "LC_MONETARY": r"(^$)|(en_US(|:.*))",
        "LC_MESSAGES": r"(^$)|(en_US(|:.*))",
        "LC_PAPER": r"(^$)|(en_US(|:.*))",
        "LC_NAME": r"(^$)|(en_US(|:.*))",
        "LC_ADDRESS": r"(^$)|(en_US(|:.*))",
        "LC_TELEPHONE": r"(^$)|(en_US(|:.*))",
        "LC_MEASUREMENT": r"(^$)|(en_US(|:.*))",
        "LC_IDENTIFICATION": r"(^$)|(en_US(|:.*))",
    }
    errors = []
    for key, expected_regex in locale_env.items():
        var_exists = True
        try:
            actual_value = os.environ[key]
        except KeyError:
            actual_value = ""
        if not var_exists or not re.match(expected_regex, actual_value):
            errors.append(
                f'Expected {key} to match "{expected_regex}", '
                + (f'but found "{actual_value}".\n' if var_exists else "but this variable is not set.\n")
            )
    if len(errors) > 0:
        raise Exception("Incorrect locale environment variable(s):\n" + "".join(errors))
