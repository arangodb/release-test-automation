#!/usr/bin/env python3

""" Release testing script"""
from pathlib import Path
import click
import tools.loghelper as lh
from arangodb.installers import RunProperties
from common_options import zip_common_options
from test_driver import TestDriver


@click.command()
@zip_common_options
def run_test(zip_package):
    """Wrapper..."""
    lh.configure_logging(True)
    test_driver = TestDriver(
        False,
        Path(""),
        Path(""),
        Path(""),
        True,
        zip_package,
        False,  # hot_backup,
        False,  # interactive,
        "all",  # starter_mode,
        False,  # stress_upgrade,
        False,  # abort_on_error,
        "127.0.0.1",
        "none",
        [],
        False,
    )
    test_driver.set_r_limits()
    test_driver.run_cleanup(RunProperties(False, False, False))


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    run_test()
