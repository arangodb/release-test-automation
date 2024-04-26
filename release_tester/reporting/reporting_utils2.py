""" utility functions/classes for allure reporting """

# pylint: disable=import-error
from arangodb.installers import RunProperties

# pylint: disable=fixme
# TODO: do not use global vars if possible
# pylint: disable=global-at-module-level
global RESULTS_DIR, CLEAN_DIR, ZIP_PACKAGE


def generate_suite_name(properties: RunProperties, versions: list, runner_type, installer_type):
    """generate test suite name for allure report"""
    if properties.enterprise:
        edition = "Enterprise"
    else:
        edition = "Community"
    if installer_type:
        package_type = installer_type
    else:
        # pylint: disable=undefined-variable
        if ZIP_PACKAGE:
            package_type = "universal binary archive"
        else:
            package_type = "deb/rpm/nsis/dmg"
    if len(versions) == 1:
        test_suite_name = (
            "ArangoDB v.{} ({}) ({} package) (enc@rest: {}) (SSL: {}) (repl v{}){} (clean install)".format(
                str(versions[0]),
                edition,
                package_type,
                "ON" if properties.encryption_at_rest else "OFF",
                "ON" if properties.ssl else "OFF",
                "2" if properties.replication2 else "1",
                " (forced OneShard)" if properties.force_one_shard else "",
            )
        )
    else:
        versions_str = " -> ".join(list(map(lambda v: "v. " + str(v), versions)))
        test_suite_name = (
            "ArangoDB ({}) ({} package) upgrade sequence: {} (enc@rest: {}) (SSL: {}) (repl v{}){}".format(
                edition,
                package_type,
                versions_str,
                "ON" if properties.encryption_at_rest else "OFF",
                "ON" if properties.ssl else "OFF",
                "2" if properties.replication2 else "1",
                " (forced OneShard)" if properties.force_one_shard else "",
            )
        )
    if runner_type:
        test_suite_name = "[" + str(runner_type) + "] " + test_suite_name

    return test_suite_name
