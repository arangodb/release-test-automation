""" utility functions/classes for allure reporting """

#pylint: disable=import-error
from arangodb.installers import RunProperties

global RESULTS_DIR, CLEAN_DIR, ZIP_PACKAGE

def generate_suite_name(properties: RunProperties, versions: list, runner_type, installer_type):
    if properties.enterprise:
        edition = "Enterprise"
    else:
        edition = "Community"
    if installer_type:
        package_type = installer_type
    else:
        if ZIP_PACKAGE:
            package_type = "universal binary archive"
        else:
            package_type = "deb/rpm/nsis/dmg"
    if len(versions) == 1:
        test_suite_name = """
    ArangoDB v.{} ({}) ({} package) (enc@rest: {}) (SSL: {}) (clean install)
                        """.format(
            str(versions[0]),
            edition,
            package_type,
            "ON" if properties.encryption_at_rest else "OFF",
            "ON" if properties.ssl else "OFF"
        )
    else:
        test_suite_name = """
                    ArangoDB v.{} ({}) {} package (upgrade from {}) (enc@rest: {}) (SSL: {})
                    """.format(
            str(versions[1]),
            edition,
            package_type,
            str(versions[0]),
            "ON" if properties.encryption_at_rest else "OFF",
            "ON" if properties.ssl else "OFF",
        )
    if runner_type:
        test_suite_name = "[" + str(runner_type) + "] " + test_suite_name

    return test_suite_name
