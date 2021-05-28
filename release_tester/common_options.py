#!/usr/bin/env python3

""" these are our common CLI options """
import sys
import click

from arangodb.starter.deployments import (
    STARTER_MODES
)

def zip_common_options(function):
    """ zip option. even on cleanup which has no more. """
    function = click.option('--zip/--no-zip', "zip_package",
                            is_flag=True,
                            default=False,
                            help='switch to zip or tar.gz package instead'
                            ' of default OS package')(function)
    return function

def very_common_options(function):
    """ These options are in all scripts """
    function = click.option('--new-version',
                            help='ArangoDB version number.',
                            default="3.8.0-nightly")(function)
    function = click.option('--verbose/--no-verbose',
                            is_flag=True,
                            default=False,
                            help='switch starter to verbose logging mode.'
                            )(function)
    function = click.option('--enterprise/--no-enterprise',
                            is_flag=True,
                            default=False,
                            help='Enterprise or community?')(function)
    function = click.option('--package-dir',
                            default='/tmp/',
                            help='directory to load the packages from.'
                            )(function)
    function = zip_common_options(function)
    return function

def common_options( support_old=True, interactive=True):
    """ these options are common to most scripts """
    def inner_func(function):
        if support_old:
            function = click.option('--old-version',
                                    help='old ArangoDB version number.',
                                    default="3.7.0-nightly")(function)
        function = click.option('--test-data-dir',
                                default='/tmp/',
                                help='directory create databases etc. in.'
                                )(function)
        function = click.option('--encryption-at-rest/--no-encryption-at-rest',
                                is_flag=True,
                                default=False,
                                help='turn on encryption at rest for Enterprise packages'
                                )(function)
        if interactive:
            function = click.option('--interactive/--no-interactive',
                                    is_flag=True,
                                    default=sys.stdout.isatty(),
                                    help='wait for the user to hit Enter?'
                                    )(function)
        function = click.option('--starter-mode',
                                default='all',
                                type=click.Choice(STARTER_MODES.keys()),
                                help='which starter deployments modes to use'
                                )(function)
        if support_old:
            function = click.option('--stress-upgrade',
                                    is_flag=True,
                                    default=False,
                                    help='launch arangobench before starting the upgrade'
                                    )(function)
        function = click.option('--abort-on-error',
                                is_flag=True,
                                default=True,
                                help='if we should abort on first error')(function)
        function = click.option('--publicip',
                                default='127.0.0.1',
                                help='IP for the click to browser hints.')(function)
        function = click.option('--selenium',
                                default='none',
                                help='if non-interactive chose the selenium target'
                                )(function)
        function = click.option('--selenium-driver-args',
                                default=[],
                                multiple=True,
                                help='options to the selenium web driver')(function)
        return function
    return inner_func

def download_options(default_source="public", double_source=False):
    """ these are options available in scripts downloading packages """
    download_sources = [
        "ftp:stage1",
        "http:stage1",
        "ftp:stage2",
        "http:stage2",
        "public"
    ]
    def inner_func(function):
        function = click.option('--enterprise-magic',
                                default='',
                                help='Enterprise or community?')(function)
        function = click.option('--force/--no-force',
                                is_flag=True,
                                default=False,
                                help='whether to overwrite existing target files or not.'
                                )(function)
        if double_source:
            function = click.option('--new-source',
                                    default=default_source,
                                    type=click.Choice(download_sources),
                                    help='where to download the package from'
                                    )(function)
            function = click.option('--old-source',
                                    default=default_source,
                                    type=click.Choice(download_sources),
                                    help='where to download the package from'
                                    )(function)
        else:
            function = click.option('--source',
                                    default=default_source,
                                    type=click.Choice(download_sources),
                                    help='where to download the package from'
                                    )(function)
        function = click.option('--httpuser',
                                default="",
                                help='user for external http download')(function)
        function = click.option('--httppassvoid',
                                default="",
                                help='passvoid for external http download'
                                )(function)
        function = click.option('--remote-host',
                                default="",
                                help='remote host to acquire packages from'
                                )(function)
        return function
    return inner_func
