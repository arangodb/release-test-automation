#!/usr/bin/env python3
""" version functions helper """


def is_higher_version(current_version, min_version):
    """check if the current version is higher than expected minimum version"""
    if current_version == min_version:
        # According to the above comparison the x.y.z-prerelease equals to x.y.z.
        # The version x.y.z-prerelease is higher then x.y.z, so the additional check must be preformed.
        # If current_version.build is None or empty then return False.
        # pylint: disable=R1719
        return True if current_version.build else False

    return current_version > min_version
