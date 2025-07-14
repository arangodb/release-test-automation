#!/usr/bin/env python3
# pylint: disable=line-too-long
# have long strings, need long lines.
""" Release testing script"""
# pylint: disable=duplicate-code
from dataclasses import dataclass
from ftplib import FTP_TLS
import os
from pathlib import Path
import platform
import json
import sys

import click
import semver
from arangodb.hot_backup_cfg import HotBackupCliCfg
from arangodb.installers import make_installer, InstallerConfig, InstallerBaseConfig, OptionGroup, tar
import arangodb.installers as installer
import tools.loghelper as lh

import requests
from common_options import very_common_options, download_options


@dataclass
class DownloadOptions(OptionGroup):
    """bearer class for base download options"""

    force: bool
    verbose: bool
    package_dir: Path
    enterprise_magic: str
    httpuser: str
    remote_host: str

class Download:
    """manage package downloading from any known arango package source"""

    # pylint: disable=too-many-arguments, disable=too-many-instance-attributes
    # pylint: disable=too-many-branches, disable=too-many-statements
    def __init__(
        self,
        bc: InstallerBaseConfig,
        options: DownloadOptions,
        version: str,
        enterprise: bool,
        source,
        existing_version_states=None,
        new_version_states=None,
        git_version="",
        force_arch="",
        force_os="",
    ):
        """main"""
        if existing_version_states is None:
            existing_version_states = {}
        if new_version_states is None:
            new_version_states = {}
        lh.section("configuration")
        if force_os != "":
            if force_os == "windows":
                tar.MACVER= [False]
                tar.WINVER= True
                installer.IS_WINDOWS = True
                installer.IS_MAC = False
            elif force_os == "mac":
                tar.MACVER=[True]
                tar.WINVER= False
                installer.IS_MAC = True
                installer.IS_WINDOWS = False
            else:
                tar.MACVER= [False]
                tar.WINVER=False
                installer.SYSTEM = "linux"
                installer.DISTRO = force_os
                installer.IS_WINDOWS = False
                installer.IS_MAC = False
        self.launch_dir = Path.cwd()
        if "WORKSPACE" in os.environ:
            self.launch_dir = Path(os.environ["WORKSPACE"])

        if not options.package_dir.is_absolute():
            options.package_dir = (self.launch_dir / options.package_dir).resolve()

        if not options.package_dir.exists() or not options.package_dir.is_dir():
            raise Exception(f"download target directory doesn't exist: {options.package_dir}")
        print("version: " + str(version))
        print("using enterpise: " + str(enterprise))
        print("using zip: " + str(bc.zip_package))
        print("package directory: " + str(options.package_dir))
        print("verbose: " + str(options.verbose))
        self.options = options
        self.is_nightly = semver.VersionInfo.parse(version).prerelease == "nightly"
        self.source = source
        if not self.is_nightly and self.source == "nightlypublic":
            self.source = "public"
        if options.remote_host != "":
            # external DNS to wuerg around docker dns issues...
            self.remote_host = options.remote_host
        else:
            # dns split horizon...
            if source in ["ftp:stage1", "ftp:stage2"]:
                self.remote_host = "nas01.arangodb.biz"
            elif source in ["http:stage2-rta"]:
                self.remote_host = "storage.googleapis.com"
            elif source in ["http:stage1-rta"]:
                self.remote_host = "storage.googleapis.com"
            elif source in ["http:stage2"]:
                self.remote_host = "download.arangodb.com"
            else:
                self.remote_host = "download.arangodb.com"
        lh.section("startup")
        arangods = []
        self.cfg = InstallerConfig(
            version=version,
            enterprise=enterprise,
            encryption_at_rest=False,
            bc=bc,
            deployment_mode="all",
            ssl=False,
            force_one_shard=False,
            use_auto_certs=False,
            arangods=arangods,
            mixed=False,
        )

        self.inst = make_installer(self.cfg)
        machine = platform.machine()
        if force_arch != "":
            machine = force_arch
            self.inst.machine = machine

        self.path_architecture = ""
        if self.is_nightly or self.cfg.semver > semver.VersionInfo.parse("3.9.99"):
            if machine == "AMD64":
                machine = "x86_64"
            self.path_architecture = machine + "/"
        self.calculate_package_names()
        self.packages = []

        self.existing_version_states = existing_version_states
        self.new_version_states = new_version_states
        self.version_content = None
        self.version_content = None
        if self.is_nightly:
            self.version_state_id = version + "_sourceInfo.log"
            if self.version_state_id in self.existing_version_states:
                self.version_content = self.existing_version_states[self.version_state_id]
            self.fresh_content = self.get_version_info(git_version)
            self.new_version_states[self.version_state_id] = self.fresh_content

    def is_different(self):
        """whether we would download a new package or not"""
        return (
            self.source == "local"
            or not self.version_content
            or not self.fresh_content
            or self.version_content != self.fresh_content
        )

    def calculate_package_names(self):
        """guess where to locate the packages"""
        self.inst.calculate_package_names()
        full_version = "v{major}.{minor}.{patch}".format(**self.cfg.semver.to_dict())
        if self.cfg.semver.prerelease is not None:
            full_version += "-" + self.cfg.semver.prerelease
        self.params = {
            "full_version": full_version,
            "major_version": "arangodb{major}{minor}".format(**self.cfg.semver.to_dict()),
            "bare_major_version": "{major}.{minor}".format(**self.cfg.semver.to_dict()),
            "remote_package_dir": self.inst.remote_package_dir,
            "path_architecture": self.path_architecture,
            "enterprise": "Enterprise" if self.cfg.enterprise else "Community",
            "enterprise_magic": self.options.enterprise_magic + "/" if self.cfg.enterprise else "",
            "packages": "" if self.is_nightly else "packages",
            "nightly": "nightly" if self.is_nightly else "",
        }
        if self.is_nightly:
            self.params["enterprise"] = ""
        else:
            self.params["path_architecture"] = ""

        self.directories = {
            "ftp:stage1": "/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "ftp:stage2": "/stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/{path_architecture}".format(
                **self.params
            ),
            "http:stage1-rta": "/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "http:stage2-rta": "/stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/{path_architecture}".format(
                **self.params
            ),
            "http:stage2": "stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/{path_architecture}".format(
                **self.params
            ),
            "nightlypublic": "{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/{path_architecture}".format(
                **self.params
            ).replace(
                "///", "/"
            ),
            "public": "{enterprise_magic}{major_version}/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ).replace("///", "/"),
            "local": None,
        }
        self.funcs = {
            "http:stage2": self.acquire_stage2_http,
            "ftp:stage1": self.acquire_stage1_ftp,
            "ftp:stage2": self.acquire_stage2_ftp,
            "http:stage1-rta": self.acquire_live_rta,
            "http:stage2-rta": self.acquire_live_rta,
            "nightlypublic": self.acquire_live,
            "public": self.acquire_live,
            "local": self.acquire_local,
        }

    # pylint: disable=unused-argument
    def acquire_local(self, directory, package, local_dir, force):
        """use the copy that we already have, hence do nothing"""
        out = local_dir / package
        if not out.exists():
            raise Exception(
                "Failed to locate package {package} in direcory {local_dir}".format(
                    **{"package": package, "local_dir": local_dir}
                )
            )

    def acquire_stage_ftp(self, directory, package, local_dir, force, stage):
        """download one file from the ftp server"""
        out = local_dir / package
        if out.exists() and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{"file": str(out)}))
            return
        ftp = FTP_TLS(self.remote_host)
        print(stage + ": " + ftp.login(user="anonymous", passwd="anonymous", acct="anonymous"))
        print(stage + ": Downloading from " + directory)
        print(stage + ": " + ftp.cwd(directory))
        ftp.set_pasv(True)
        try:
            with out.open(mode="wb") as filedes:
                print(stage + ": downloading from " + directory + " to " + str(out))
                print(stage + ": " + ftp.retrbinary("RETR " + package, filedes.write))
        except Exception as ex:
            print(f"caught {ex} while trying to download")
            print(f"directory listing: {ftp.retrlines('LIST')}")
            print(f"deleting {out}")
            out.unlink()
            raise ex
    def acquire_stage_http(self, directory, package, local_dir, force, stage):
        """download one file via http"""
        url = "https://{user}:{passvoid}@{remote_host}:8529/{dir}{pkg}".format(
            **{
                "remote_host": self.remote_host,
                "user": self.options.httpuser,
                "dir": directory,
                "pkg": package,
            }
        )

        out = local_dir / package
        if out.exists() and out.stat().st_size > 500 and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{"file": str(out)}))
            return
        print(stage + ": downloading " + str(url))
        retry = 0
        while retry < 99:
            try:
                res = requests.get(url, timeout=120)
                retry = 100
            except requests.exceptions.ChunkedEncodingError as ex:
                print(f"failed to download {url} try {retry} - {ex} - retrying.")
                retry += 1
        if res.status_code == 200:
            print(
                stage
                + ": writing {size} kbytes to {file}".format(**{"size": str(len(res.content) / 1024), "file": str(out)})
            )
            out.write_bytes(res.content)
        else:
            raise Exception(
                stage
                + ": failed to download {url} - {error} - {msg}".format(
                    **{"url": url, "error": res.status_code, "msg": res.text}
                )
            )

    def acquire_stage2_http(self, directory, package, local_dir, force):
        """download stage 2 from http"""
        self.acquire_stage_http(directory, package, local_dir, force, "STAGE_2_HTTP")

    def acquire_stage1_ftp(self, directory, package, local_dir, force):
        """download stage 1 from ftp"""
        self.acquire_stage_ftp(directory, package, local_dir, force, "STAGE_1_FTP")

    def acquire_stage2_ftp(self, directory, package, local_dir, force):
        """download stage 2 from ftp"""
        self.acquire_stage_ftp(directory, package, local_dir, force, "STAGE_2_FTP")

    def acquire_live(self, directory, package, local_dir, force):
        """download live files via http"""
        print("live")
        url = "https://{remote_host}/{dir}{pkg}".format(
            **{"remote_host": self.remote_host,
               "dir": directory.replace('//','/').replace('//', '/'),
               "pkg": package}
        )
        self._acquire_live(url, package, local_dir, force, "LIVE")

    def acquire_live_rta(self, directory, package, local_dir, force):
        """download live files via http"""
        url = "https://{remote_host}/gcr-for-rta{dir}{pkg}".format(
            **{"remote_host": self.remote_host,
               "dir": directory.replace('//','/').replace('//', '/'),
               "pkg": package}
        )
        self._acquire_live(url, package, local_dir, force, "RTA-LIVE")

    def _acquire_live(self, url, package, local_dir, force, which):
        out = local_dir / package
        exists = out.exists()
        if exists and not force:
            print(f"{which}: not overwriting {str(out)} since not forced to overwrite!")
            return
        print(f"{which}: downloading {str(url)}")
        retry = 0
        while retry < 99:
            try:
                res = requests.get(url, timeout=120)
                retry = 100
            except requests.exceptions.ConnectionError as ex:
                print(f"{which}: failed to download {url} try {retry} - {ex} - retrying.")
                retry += 1
            except requests.exceptions.ChunkedEncodingError as ex:
                print(f"{which}: failed to download {url} try {retry} - {ex} - retrying.")
                retry += 1
        if res.status_code == 200:
            print(
                "{which}: writing {size} kbytes to {existing}{file}".format(
                    **{
                        "size": str(len(res.content) / 1024),
                        "file": str(out),
                        "existing": "existing " if exists else "",
                        "which": which,
                    }
                )
            )
            out.write_bytes(res.content)
        else:
            raise Exception(
                "{which}: failed to download {url} - {error} - {msg}".format(
                    **{"url": url, "error": res.status_code, "msg": res.text, "which": which}
                )
            )

    def get_packages(self, force):
        """download all packages for this version from the specified package source"""
        ret = []
        self.packages = []
        if self.inst.server_package:
            self.packages.append(self.inst.server_package)
        if self.inst.client_package:
            self.packages.append(self.inst.client_package)
        if self.inst.debug_package:
            self.packages.append(self.inst.debug_package)

        for package in self.packages:
            self.funcs[self.source](self.directories[self.source], package, Path(self.options.package_dir), force)
            ret.append(Path(self.options.package_dir) / package)
        return ret

    def get_version_info(self, git_version):
        """download the nightly sourceInfo.json file, calculate more precise version of the packages"""
        if self.source == "local":
            return ""
        source_info_fn = "sourceInfo.json"
        self.funcs[self.source](self.directories[self.source], source_info_fn, Path(self.options.package_dir), True)
        text = (Path(self.options.package_dir) / source_info_fn).read_text()
        while text[0] != "{":
            text = text[1:]
        val = json.loads(text)
        val["GIT_VERSION"] = git_version
        version = val["VERSION"].replace("-devel", "")
        self.inst.reset_version(version + "-nightly" if self.is_nightly else "")
        self.cfg.reset_version(self.inst.cfg.version)
        self.calculate_package_names()
        return json.dumps(val)


@click.command()
@very_common_options()
@download_options()
# fmt: off
def main(**kwargs):
    """ main """
    kwargs['interactive'] = False
    kwargs['abort_on_error'] = False
    kwargs['package_dir'] = Path(kwargs['package_dir'])
    kwargs['test_data_dir'] = Path()
    kwargs['alluredir'] = Path()
    kwargs['starter_mode'] = 'all'
    kwargs['stress_upgrade'] = False
    kwargs['publicip'] = "127.0.0.1"
    kwargs['hb_mode'] = "disabled"
    kwargs['hb_storage_path_prefix'] = ""
    kwargs['hb_provider'] = ""
    kwargs['is_instrumented'] = False

    kwargs['hb_cli_cfg'] = HotBackupCliCfg("disabled","","","","","","")
    kwargs['test'] = ''
    kwargs['skip'] = ''
    kwargs['base_config'] = InstallerBaseConfig.from_dict(**kwargs)

    dl_opts = DownloadOptions.from_dict(**kwargs)
    lh.configure_logging(kwargs['verbose'])
    downloader = Download(
        bc=kwargs['base_config'],
        options=dl_opts,
        version=kwargs['new_version'],
        enterprise=kwargs['enterprise'],
        source=kwargs['source'],
        force_arch=kwargs['force_arch'],
        force_os=kwargs['force_os'])
    return downloader.get_packages(kwargs['force'])


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
