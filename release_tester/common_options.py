#!/usr/bin/env python3

""" these are our common CLI options """
from pathlib import Path
import sys
import os
import click

from arangodb.starter.deployments import STARTER_MODES
from arangodb.installers import HB_MODES, HB_PROVIDERS

CWD = Path.cwd()


def get_default_value(env_key: str, add_subkey: str, default_value: str):
    """try to extract default values from the environment"""
    if env_key in os.environ:
        return os.environ[env_key] + add_subkey
    return default_value


def get_default_path_value(env_key: str, add_path: str, default_path: Path):
    """try to extract jenkins default path values"""
    if env_key in os.environ:
        return Path(os.environ[env_key]) / add_path
    return default_path


def zip_common_options(function):
    """zip option. even on cleanup which has no more."""
    function = click.option(
        "--zip/--no-zip",
        "zip_package",
        is_flag=True,
        default=False,
        help="switch to zip or tar.gz package instead" " of default OS package",
    )(function)
    function = click.option(
        "--src/--no-src",
        "src_testing",
        is_flag=True,
        default=False,
        help="switch to source directory instead" " of default OS package",
    )(function)
    return function


def hotbackup_options():
    """all of these hot backup options
    => arangodb.installers.HotBackupCliCfg"""
    access_key_id = get_default_value("AWS_ACCESS_KEY_ID", "", "")
    secret_access_key = get_default_value("AWS_SECRET_ACCESS_KEY", "", "")
    region = get_default_value("AWS_REGION", "", "")
    acl = get_default_value("AWS_ACL", "", "private")

    def inner_func(function):
        function = click.option(
            "--hb-mode",
            "hb_mode",
            default="directory",
            type=click.Choice(HB_MODES.keys()),
            help="which type of hot backup to use",
        )(function)
        function = click.option(
            "--hb-provider",
            "hb_provider",
            default=None,
            type=click.Choice(HB_PROVIDERS.keys()),
            help="which storage provider to use for hot backup",
        )(function)
        function = click.option(
            "--hb-storage-path-prefix",
            "hb_storage_path_prefix",
            default="",
            help="directory to store hot backups on the cloud storage",
        )(function)
        function = click.option(
            "--hb-aws-access-key-id",
            "hb_aws_access_key_id",
            default=access_key_id,
            help="AWS access key id",
        )(function)
        function = click.option(
            "--hb-aws-secret-access-key",
            "hb_aws_secret_access_key",
            default=secret_access_key,
            help="AWS secret access key",
        )(function)
        function = click.option(
            "--hb-aws-region",
            "hb_aws_region",
            default=region,
            help="AWS region",
        )(function)
        function = click.option(
            "--hb-aws-acl",
            "hb_aws_acl",
            default=acl,
            help="AWS  ACL (default value: 'private')",
        )(function)
        function = click.option(
            "--hb-use-cloud-preset",
            "hb_use_cloud_preset",
            default=None,
            help="Use hotbackup options presaved in a secret location.",
        )(function)
        function = click.option(
            "--hb-gce-service-account-credentials",
            "hb_gce_service_account_credentials",
            default=None,
            help="GCE service account credentials(JSON string).",
        )(function)
        function = click.option(
            "--hb-gce-service-account-file",
            "hb_gce_service_account_file",
            default=None,
            help="Path to a JSON file containing GCE service account credentials.",
        )(function)
        function = click.option(
            "--hb-gce-project-number",
            "hb_gce_project_number",
            default=None,
            help="GCE project ID.",
        )(function)
        function = click.option(
            "--hb-azure-account",
            "hb_azure_account",
            default=None,
            help="Azure storage account.",
        )(function)
        function = click.option(
            "--hb-azure-key",
            "hb_azure_key",
            default=None,
            help="Azure storage account access key.",
        )(function)
        return function

    return inner_func


def test_suite_filtering_options():
    """options for running arbitrary sets of test suites, test cases"""

    def inner_func(function):
        function = click.option(
            "--include-test-suite",
            "include_test_suites",
            default=[],
            type=click.STRING,
            multiple=True,
            help="List of test suite names to run. To define a list of suites, ",
        )(function)
        function = click.option(
            "--exclude-test-suite",
            "exclude_test_suites",
            default=[],
            type=click.STRING,
            multiple=True,
            help="Run all known test suites except these.",
        )(function)
        return function

    return inner_func


def very_common_options(support_multi_version=False):
    """These options are in all scripts
    most => arangodb.installers.InstallerBaseConfig"""
    package_dir = Path("/home/package_cache/")

    if not package_dir.exists():
        package_dir = CWD / "package_cache"

    if not package_dir.exists():
        package_dir = Path("/tmp/")
    package_dir = get_default_path_value("WORKSPACE", "package_cache", package_dir)

    defver = get_default_value("NEW_VERSION", "", "3.10.0-nightly")
    if support_multi_version:
        defver = [defver]

    def inner_func(function):
        function = click.option(
            "--new-version",
            multiple=support_multi_version,
            help="ArangoDB version number.",
            default=defver,
        )(function)
        function = click.option(
            "--verbose/--no-verbose",
            is_flag=True,
            default=False,
            help="switch starter to verbose logging mode.",
        )(function)
        function = click.option(
            "--enterprise/--no-enterprise",
            is_flag=True,
            default=False,
            help="Enterprise or community?",
        )(function)
        function = click.option(
            "--package-dir",
            default=package_dir,
            help="directory to down/load the packages from/to.",
        )(function)
        function = zip_common_options(function)
        return function

    return inner_func


def common_options(
    support_old=True,
    interactive=True,
    test_data_dir="/tmp/",
    support_multi_version=False,
):
    """these options are common to most scripts
    most => arangodb.installers.InstallerBaseConfig"""

    test_data_dir = get_default_path_value("WORKSPACE", "test_dir", test_data_dir)
    default_allure_dir = Path("/home/allure-results")
    if not default_allure_dir.exists():
        default_allure_dir = get_default_path_value("WORKSPACE", "allure-results", CWD / "allure-results")

    def inner_func(function):

        if support_old:
            defver = get_default_value("OLD_VERSION", "", "3.9-nightly")
            if support_multi_version:
                defver = [defver]
            function = click.option(
                "--old-version",
                multiple=support_multi_version,
                help="old ArangoDB version number.",
                default=defver,
            )(function)
        function = click.option(
            "--test-data-dir",
            default=test_data_dir,
            help="directory create databases etc. in.",
        )(function)
        function = click.option(
            "--encryption-at-rest/--no-encryption-at-rest",
            is_flag=True,
            default=False,
            help="turn on encryption at rest for Enterprise packages",
        )(function)
        if interactive:
            function = click.option(
                "--interactive/--no-interactive",
                is_flag=True,
                default=sys.stdout.isatty(),
                help="wait for the user to hit Enter?",
            )(function)
        function = click.option(
            "--starter-mode",
            default="all",
            type=click.Choice(STARTER_MODES.keys()),
            help="which starter deployments modes to use",
        )(function)
        if support_old:
            function = click.option(
                "--stress-upgrade",
                is_flag=True,
                default=False,
                help="launch arangobench before starting the upgrade",
            )(function)
        function = click.option(
            "--abort-on-error/--do-not-abort-on-error",
            is_flag=True,
            default=True,
            help="if we should abort on first error",
        )(function)
        function = click.option("--publicip", default="127.0.0.1", help="IP for the click to browser hints.")(function)
        function = click.option(
            "--selenium",
            default="none",
            help="if non-interactive chose the selenium target",
        )(function)
        function = click.option(
            "--selenium-driver-args",
            default=[],
            multiple=True,
            help="options to the selenium web driver",
        )(function)
        function = click.option(
            "--clean-alluredir/--do-not-clean-alluredir",
            is_flag=True,
            default=True,
            help="clean allure results dir before running tests",
        )(function)
        function = click.option(
            "--alluredir",
            default=default_allure_dir,
            help="directory to store allure results",
        )(function)
        function = click.option("--ssl/--no-ssl", is_flag=True, default=False, help="use SSL")(function)
        function = click.option(
            "--use-auto-certs",
            is_flag=True,
            default=False,
            help="use self-signed SSL certs",
        )(function)
        return function

    return inner_func


def download_options(default_source="public", double_source=False, other_source=False):
    """these are options available in scripts downloading packages"""
    download_sources = ["http:stage1", "http:stage2", "nightlypublic", "public", "local"]

    def inner_func(function):
        default_local_httpuser = get_default_value("RTA_LOCAL_HTTPUSER", "", "")
        function = click.option("--enterprise-magic", default="", help="Enterprise or community?")(function)
        function = click.option(
            "--force/--no-force",
            is_flag=True,
            default=False,
            help="whether to overwrite existing target files or not.",
        )(function)
        if double_source:
            function = click.option(
                "--new-source",
                default=default_source,
                type=click.Choice(download_sources),
                help="where to download the package from",
            )(function)
            function = click.option(
                "--old-source",
                default=default_source,
                type=click.Choice(download_sources),
                help="where to download the package from",
            )(function)
        else:
            function = click.option(
                "--source",
                default=default_source,
                type=click.Choice(download_sources),
                help="where to download the package from",
            )(function)
        if other_source:
            function = click.option(
                "--other-source",
                default=default_source,
                type=click.Choice(download_sources),
                help="where to download the secondary package from",
            )(function)
        function = click.option("--httpuser", default=default_local_httpuser, help="user for external http download")(
            function
        )
        function = click.option("--remote-host", default="", help="remote host to acquire packages from")(function)
        return function

    return inner_func


def full_common_options(function):
    """full test/& upgrade options"""
    function = click.option(
        "--git-version",
        default="",
        help="specify the output of: git rev-parse --verify HEAD",
    )(function)
    function = click.option(
        "--edition",
        "editions",
        default=["EE", "EP", "C"],
        multiple=True,
        help="which editions to run EE => enterprise Encryption@rest, EP => enterprise, C => community",
    )(function)
    return function
