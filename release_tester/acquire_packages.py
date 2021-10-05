#!/usr/bin/env python3
# pylint: disable=C0301
# have long strings, need long lines.
""" Release testing script"""
from ftplib import FTP
from pathlib import Path
import json
import sys
import click
from arangodb.installers import make_installer, InstallerConfig
import tools.loghelper as lh

import requests
from common_options import very_common_options, download_options


class AcquirePackages:
    """manage package downloading from any known arango package source"""

    # pylint: disable=R0913 disable=R0902
    def __init__(
        self,
        version,
        verbose,
        package_dir,
        enterprise,
        enterprise_magic,
        zip_package,
        source,
        httpuser,
        httppassvoid,
        remote_host,
    ):
        """main"""
        lh.section("configuration")
        print("version: " + str(version))
        print("using enterpise: " + str(enterprise))
        print("using zip: " + str(zip_package))
        print("package directory: " + str(package_dir))
        print("verbose: " + str(verbose))
        self.user = httpuser
        self.passvoid = httppassvoid
        self.enterprise_magic = enterprise_magic
        if remote_host != "":
            # external DNS to wuerg around docker dns issues...
            self.remote_host = remote_host
        else:
            # dns split horizon...
            if source in ["ftp:stage1", "ftp:stage2"]:
                self.remote_host = "Nas02.arangodb.biz"
            elif source in ["http:stage1", "http:stage2"]:
                self.remote_host = "fileserver.arangodb.com"
            else:
                self.remote_host = "download.arangodb.com"
        lh.section("startup")

        self.package_dir = Path(package_dir)
        self.cfg = InstallerConfig(
            version,
            verbose,
            enterprise,
            False,  # don't care for enc at rest
            zip_package,
            self.package_dir,
            Path("/"),
            "",
            "127.0.0.1",
            False,
            False,
        )
        self.inst = make_installer(self.cfg)
        self.is_nightly = self.inst.semver.prerelease == "nightly"
        self.calculate_package_names()
        self.packages = []

    def calculate_package_names(self):
        """guess where to locate the packages"""
        if self.is_nightly:
            self.inst.calculate_package_names()
        self.params = {
            "full_version": "v{major}.{minor}.{patch}".format(**self.cfg.semver.to_dict()),
            "major_version": "arangodb{major}{minor}".format(**self.cfg.semver.to_dict()),
            "bare_major_version": "{major}.{minor}".format(**self.cfg.semver.to_dict()),
            "remote_package_dir": self.inst.remote_package_dir,
            "enterprise": "Enterprise" if self.cfg.enterprise else "Community",
            "enterprise_magic": self.enterprise_magic + "/" if self.cfg.enterprise else "",
            "packages": "" if self.is_nightly else "packages",
            "nightly": "nightly" if self.is_nightly else "",
        }
        if self.is_nightly:
            self.params["enterprise"] = ""

        self.directories = {
            "ftp:stage1": "/buildfiles/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "ftp:stage2": "/buildfiles/stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "http:stage1": "stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "http:stage2": "stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ),
            "nightlypublic": "{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ).replace("///", "/"),
            "public": "{enterprise_magic}{major_version}/{enterprise}/{remote_package_dir}/".format(
                **self.params
            ).replace("///", "/"),
        }
        self.funcs = {
            "http:stage1": self.acquire_stage1_http,
            "http:stage2": self.acquire_stage2_http,
            "ftp:stage1": self.acquire_stage1_ftp,
            "ftp:stage2": self.acquire_stage2_ftp,
            "nightlypublic": self.acquire_live,
            "public": self.acquire_live,
        }

    def acquire_stage_ftp(self, directory, package, local_dir, force, stage):
        """download one file from the ftp server"""
        out = local_dir / package
        if out.exists() and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{"file": str(out)}))
            return
        ftp = FTP(self.remote_host)
        print(stage + ": " + ftp.login(user="anonymous", passwd="anonymous", acct="anonymous"))
        print(stage + ": Downloading from " + directory)
        print(stage + ": " + ftp.cwd(directory))
        ftp.set_pasv(True)
        with out.open(mode="wb") as filedes:
            print(stage + ": downloading from " + directory + " to " + str(out))
            print(stage + ": " + ftp.retrbinary("RETR " + package, filedes.write))

    def acquire_stage_http(self, directory, package, local_dir, force, stage):
        """download one file via http"""
        url = "https://{user}:{passvoid}@{remote_host}:8529/{dir}{pkg}".format(
            **{
                "remote_host": self.remote_host,
                "passvoid": self.passvoid,
                "user": self.user,
                "dir": directory,
                "pkg": package,
            }
        )

        out = local_dir / package
        if out.exists() and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{"file": str(out)}))
            return
        print(stage + ": downloading " + str(url))
        res = requests.get(url)
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

    def acquire_stage1_http(self, directory, package, local_dir, force):
        """download stage 1 from http"""
        self.acquire_stage_http(directory, package, local_dir, force, "STAGE_1_HTTP")

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
            **{"remote_host": self.remote_host, "dir": directory, "pkg": package}
        )

        out = local_dir / package
        if out.exists() and not force:
            print("LIVE: not overwriting {file} since not forced to overwrite!".format(**{"file": str(out)}))
            return
        print("LIVE: downloading " + str(url))
        res = requests.get(url)
        if res.status_code == 200:
            print(
                "LIVE: writing {size} kbytes to {file}".format(
                    **{"size": str(len(res.content) / 1024), "file": str(out)}
                )
            )
            out.write_bytes(res.content)
        else:
            raise Exception(
                "LIVE: failed to download {url} - {error} - {msg}".format(
                    **{"url": url, "error": res.status_code, "msg": res.text}
                )
            )

    def get_packages(self, force, source):
        """download all packages for this version from the specified package source"""
        self.packages = [self.inst.server_package]
        if self.inst.client_package:
            self.packages.append(self.inst.client_package)
        if self.inst.debug_package:
            self.packages.append(self.inst.debug_package)

        for package in self.packages:
            self.funcs[source](self.directories[source], package, Path(self.package_dir), force)

    def get_version_info(self, source, git_version):
        """download the nightly sourceInfo.json file, calculate more precise version of the packages"""
        source_info_fn = "sourceInfo.json"
        self.funcs[source](self.directories[source], source_info_fn, Path(self.package_dir), True)
        text = (self.package_dir / source_info_fn).read_text()
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
# pylint: disable=R0913
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package,
        # download options:
        enterprise_magic, force, source,
        httpuser, httppassvoid, remote_host):
# fmt: on
    """ main wrapper """
    lh.configure_logging(verbose)
    downloader = AcquirePackages(
        new_version,
        verbose,
        package_dir,
        enterprise,
        enterprise_magic,
        zip_package,
        source,
        httpuser,
        httppassvoid,
        remote_host,
    )
    return downloader.get_packages(force, source)


if __name__ == "__main__":
    # pylint: disable=E1120 # fix clickiness.
    sys.exit(main())
