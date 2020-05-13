#!/usr/bin/env python3
""" run an installer for the detected operating system """
import platform
import os
from pathlib import Path


class InstallConfig():
    """ stores the baseline of this environment """
    def __init__(self, version, verbose, enterprise, package_dir, publicip, quote_user):
        self.publicip = publicip
        self.quote_user = quote_user
        self.username = "root"
        self.passvoid = "abc"
        self.enterprise = enterprise
        self.version = version
        self.verbose = verbose
        self.package_dir = package_dir
        self.install_prefix = Path("/")
        self.jwt = ''
        self.port = 8529
        self.localhost = 'localhost'
        self.all_instances = {}
        self.pwd = Path(os.path.dirname(os.path.realpath(__file__)))
        self.test_data_dir = self.pwd / '..' / '..' / '..' / 'test_data'
        self.frontends = []
        super().__init__()

    def add_frontend(self, proto, ip, port):
        self.frontends.append({
            'proto': proto,
            'ip': ip,
            'port': port
            })

    def generate_password(self):
        """ generate a new password """
        self.passvoid = 'cde'


#pylint: disable=import-outside-toplevel
def get(*args, **kwargs):
    """ detect the OS and its distro,
        choose the proper installer
        and return it"""
    winver = platform.win32_ver()
    if winver[0]:
        from arangodb.installers.nsis import InstallerW
        return InstallerW(InstallConfig(*args, **kwargs))

    import resource
    nofd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
    if nofd < 10000:
        raise Exception("please use ulimit -n to adjust the number of allowed filedescriptors - currently have: " + str(nofd))
    macver = platform.mac_ver()
    if macver[0]:
        from arangodb.installers.mac import InstallerMac
        return InstallerMac(InstallConfig(*args, **kwargs))

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
