#!/usr/bin/env python3
""" version functions helper """


def is_higher_version(current_version, min_version):
    """check if the current version is higher than expected minimum version"""
    if current_version == min_version:
        # The version x.y.z-prerelease is the same but check if it is a devel build.
        return current_version.build != ''

    return current_version > min_version
