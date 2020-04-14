#!/usr/bin/env python3
""" run an installer for the detected operating system """
import platform
from pathlib import Path


class InstallConfig():
    """ stores the baseline of this environment """
    def __init__(self, version, enterprise, package_dir, publicip):
        self.publicip = publicip
        self.username = "root"
        self.passvoid = "abc"
        self.enterprise = enterprise
        self.version = version
        self.package_dir = package_dir
        self.install_prefix = Path("/")
        self.jwt = ''
        self.port = 8529
        self.localhost = 'localhost'
        self.all_instances = {}

    def generate_password(self):
        """ generate a new password """
        self.passvoid = 'cde'


def get(*args, **kwargs):
    """ detect the OS and its distro,
        choose the proper installer
        and return it"""
    winver = platform.win32_ver()
    if winver[0]:
        from arangodb.installers.nsis import InstallerW
        return InstallerW(InstallConfig(*args, **kwargs))
    macver = platform.mac_ver()
    if macver[0]:
        raise Exception("mac not yet implemented")

    if platform.system() == "linux" or platform.system() == "Linux":
        import distro
        distro = distro.linux_distribution(full_distribution_name=False)

        if distro[0] in ['debian', 'ubuntu']:
            from arangodb.installers.deb import InstallerDeb
            return InstallerDeb(InstallConfig(*args, **kwargs))
        if distro[0] in ['centos', 'redhat', 'suse']:
            from arangodb.installers.rpm import InstallerRPM
            return InstallerRPM(InstallConfig(*args, **kwargs))
        raise Exception('unsupported linux distribution: ' + distro)
    raise Exception('unsupported os' + platform.system())
