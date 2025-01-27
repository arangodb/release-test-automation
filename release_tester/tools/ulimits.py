#!/usr/bin/env python3
""" tool to check whether ulimits suit our needs and possibly adjust """
import platform

WINVER = platform.win32_ver()

def detect_file_ulimit():
    """check whether the ulimit for files is to low"""
    if not WINVER[0]:
        # pylint: disable=import-outside-toplevel
        import resource

        nofd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
        if nofd < 65535:
            raise Exception(
                "please use ulimit -n <count>"
                " to adjust the number of allowed"
                " filedescriptors to a value greater"
                " or equal 65535. Currently you have"
                " set the limit to: " + str(nofd)
            )
        giga_byte = 2**30
        resource.setrlimit(resource.RLIMIT_CORE, (giga_byte, giga_byte))
