#!/usr/bin/env python3
"""steps for the installation"""
from reporting.reporting_utils import step
# pylint: disable=broad-except

@step
def check_if_server_packages_can_be_installed_consequentially(installer1, installer2, expect_success=True):
    """check if two packages can be installed one over another"""
    first_package_name = installer1.server_package
    second_package_name = installer2.server_package
    installer1.install_server_package()
    try:
        installer2.upgrade_server_package(installer1)
        if expect_success:
            installer2.check_installed_files()
            return
        raise Exception(
            f"Package {second_package_name} can be installed over {first_package_name}. A conflict was expected!"
        )
    except Exception as ex:
        if not expect_success:
            return
        raise Exception(
            f"Package {second_package_name} can not be installed over {first_package_name}. Success was expected!"
        ) from ex


@step
def check_if_client_packages_can_be_installed_consequentially(installer1, installer2, expect_success=True):
    """check if two client packages can be installed one over another"""
    first_package_name = installer1.client_package
    second_package_name = installer2.client_package
    installer1.install_client_package()
    try:
        installer2.upgrade_client_package(installer1)
    except Exception as ex:
        if expect_success:
            raise Exception(
                f"Package {second_package_name} can not be installed over {first_package_name}. Success was expected!"
            ) from ex
        return
    if not expect_success:
        raise Exception(
            f"Package {second_package_name} can be installed over {first_package_name}. A conflict was expected!"
        )
    installer2.check_installed_files()


@step
def check_if_debug_package_can_be_installed_over_server_package(debug_installer, server_installer, expect_success=True):
    """check if client package can be installed after server package"""
    debug_package_name = debug_installer.debug_package
    server_package_name = server_installer.server_package
    server_installer.install_server_package()
    try:
        debug_installer.install_debug_package()
        if not expect_success:
            raise Exception(
                f"Package {debug_package_name} can be installed over {server_package_name}. A conflict was expected!"
            )
    except Exception as ex:
        if not expect_success:
            pass
        else:
            raise Exception(
                f"Package {debug_package_name} can not be installed over {server_package_name}. Success was expected!"
            ) from ex
    debug_installer.gdb_test()


@step
def check_if_client_package_can_be_installed_over_server_package(
    client_installer, server_installer, expect_success=False
):
    """check if debug package can be installed after server package"""
    client_package_name = client_installer.client_package
    server_package_name = server_installer.server_package
    server_installer.install_server_package()
    try:
        client_installer.install_client_package()
        if expect_success:
            client_installer.check_installed_files()
        else:
            raise Exception(
                f"Package {client_package_name} can be installed over {server_package_name}. A conflict was expected!"
            )
    except Exception as ex:
        if expect_success:
            raise Exception(
                f"Package {client_package_name} can not be installed over {server_package_name}. Success was expected!"
            ) from ex


@step
def check_if_client_package_can_be_installed(client_installer, expect_success=True):
    """check if client package can be installed"""
    client_package_name = client_installer.client_package
    try:
        client_installer.install_client_package()
    except Exception as ex:
        if not expect_success:
            pass
        else:
            raise Exception(f"Package {client_package_name} can not be installed. Success was expected!") from ex
    if expect_success:
        client_installer.check_installed_files()
    else:
        raise Exception(f"Package {client_package_name} can be installed. An error was expected!")


@step
def check_if_server_package_can_be_installed(server_installer, expect_success=True):
    """check if client package can be installed"""
    package_name = server_installer.server_package
    try:
        server_installer.install_server_package()
    except Exception as ex:
        if not expect_success:
            pass
        else:
            raise Exception(f"Package {package_name} can not be installed. Success was expected!") from ex
    if expect_success:
        server_installer.check_installed_files()
    else:
        raise Exception(f"Package {package_name} can be installed. An error was expected!")


@step
def check_if_debug_package_can_be_installed(debug_installer, expect_success=True):
    """check if debug package can be installed after server package"""
    debug_package_name = debug_installer.debug_package
    try:
        debug_installer.install_debug_package()
        if not expect_success:
            raise Exception(f"Package {debug_package_name} can be installed. An error was expected!")
    except Exception as ex:
        if not expect_success:
            pass
        else:
            raise Exception(f"Package {debug_package_name} can not be installed. Success was expected!") from ex
