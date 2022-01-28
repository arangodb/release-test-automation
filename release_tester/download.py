#!/usr/bin/env python3
# pylint: disable=line-too-long
# have long strings, need long lines.
""" Release testing script"""
from ftplib import FTP
from io import BytesIO
import os
from pathlib import Path
import json
import sys
import tarfile

import click
from arangodb.installers import make_installer, InstallerConfig
import tools.loghelper as lh

import requests
from common_options import very_common_options, download_options


def get_tar_file_path(base_directory, versions, package_target):
    """calculate the name of the versions tar file"""
    return base_directory / f"Upgrade_{versions[0]}__{versions[1]}_{package_target}_version.tar"


def touch_all_tars_in_dir(tar_file):
    """sets the current filestamp to all tars so jenkins preserves them"""
    print("touching " + str(tar_file))
    tar_file.touch()
    directory = tar_file.parent
    if not directory.is_dir():
        print("we don't seem to have found a dir from the tarfile? " + str(directory))
        return
    for one_file in directory.iterdir():
        if str(one_file).endswith("version.tar"):
            print("touching " + str(one_file))
            one_file.touch()
        # else:
        #    print("doing nothing about " + str(one_file))


def read_versions_tar(tar_file, versions):
    """reads the versions tar"""
    try:
        fdesc = tar_file.open("rb")
        with tarfile.open(fileobj=fdesc, mode="r:") as tar:
            for member in tar:
                print(member.name)
                print(member.isfile())
                if member.isfile():
                    versions[member.name] = tar.extractfile(member).read().decode(encoding="utf-8")
                    print(versions[member.name])
            tar.close()
        fdesc.close()
    except FileNotFoundError:
        pass


def write_version_tar(tar_file, versions):
    """write the versions tar"""
    print("writing " + str(tar_file))
    fdesc = tar_file.open("wb")
    with tarfile.open(fileobj=fdesc, mode="w:") as tar:
        for version_name in versions:
            data = versions[version_name].encode("utf-8")
            print(version_name)
            print(versions[version_name])
            file_obj = BytesIO(data)
            info = tarfile.TarInfo(name=version_name)
            info.size = len(data)
            tar.addfile(tarinfo=info, fileobj=file_obj)
        tar.close()
    fdesc.close()


class DownloadOptions:
    """bearer class for base download options"""

    # pylint: disable=too-many-arguments disable=too-few-public-methods disable=too-many-instance-attributes
    def __init__(
        self,
        force_dl: bool,
        verbose: bool,
        package_dir: Path,
        enterprise_magic: str,
        httpuser: str,
        httppassvoid: str,
        remote_host: str,
    ):
        self.launch_dir = Path.cwd()
        if "WORKSPACE" in os.environ:
            self.launch_dir = Path(os.environ["WORKSPACE"])
        self.force_dl = force_dl
        self.verbose = verbose
        if not package_dir.is_absolute():
            package_dir = (self.launch_dir / package_dir).resolve()
        self.package_dir = package_dir
        self.enterprise_magic = enterprise_magic
        self.httpuser = httpuser
        self.httppassvoid = httppassvoid
        self.remote_host = remote_host


class Download:
    """manage package downloading from any known arango package source"""

    # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=dangerous-default-value
    def __init__(
        self,
        options: DownloadOptions,
        version,
        enterprise,
        zip_package,
        source,
        existing_version_states={},
        new_version_states={},
        git_version="",
    ):
        """main"""
        lh.section("configuration")
        print("version: " + str(version))
        print("using enterpise: " + str(enterprise))
        print("using zip: " + str(zip_package))
        print("package directory: " + str(options.package_dir))
        print("verbose: " + str(options.verbose))
        self.options = options
        self.source = source
        if options.remote_host != "":
            # external DNS to wuerg around docker dns issues...
            self.remote_host = options.remote_host
        else:
            # dns split horizon...
            if source in ["ftp:stage1", "ftp:stage2"]:
                self.remote_host = "Nas02.arangodb.biz"
            elif source in ["http:stage1", "http:stage2"]:
                self.remote_host = "fileserver.arangodb.com"
            else:
                self.remote_host = "download.arangodb.com"
        lh.section("startup")
        self.cfg = InstallerConfig(
            version=version,
            verbose=options.verbose,
            enterprise=enterprise,
            encryption_at_rest=False,
            zip_package=zip_package,
            hot_backup="disabled",  # don't care
            package_dir=options.package_dir,
            test_dir=Path("/"),
            deployment_mode="all",
            publicip="127.0.0.1",
            interactive=False,
            stress_upgrade=False,
            ssl=False,
        )
        self.inst = make_installer(self.cfg)
        self.is_nightly = self.inst.semver.prerelease == "nightly"
        self.calculate_package_names()
        self.packages = []

        self.existing_version_states = existing_version_states
        self.new_version_states = new_version_states
        self.version_content = None
        self.version_content = None
        if version.find("-nightly") >= 0:
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
        self.params = {
            "full_version": "v{major}.{minor}.{patch}".format(**self.cfg.semver.to_dict()),
            "major_version": "arangodb{major}{minor}".format(**self.cfg.semver.to_dict()),
            "bare_major_version": "{major}.{minor}".format(**self.cfg.semver.to_dict()),
            "remote_package_dir": self.inst.remote_package_dir,
            "enterprise": "Enterprise" if self.cfg.enterprise else "Community",
            "enterprise_magic": self.options.enterprise_magic + "/" if self.cfg.enterprise else "",
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
            "local": None,
        }
        self.funcs = {
            "http:stage1": self.acquire_stage1_http,
            "http:stage2": self.acquire_stage2_http,
            "ftp:stage1": self.acquire_stage1_ftp,
            "ftp:stage2": self.acquire_stage2_ftp,
            "nightlypublic": self.acquire_live,
            "public": self.acquire_live,
            "local": self.acquire_none,
        }

    # pylint: disable=unused-argument disable=no-self-use
    def acquire_none(self, directory, package, local_dir, force):
        """use the copy that we already have, hence do nothing"""
        print("skipping download")

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
                "passvoid": self.options.httppassvoid,
                "user": self.options.httpuser,
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

    def get_packages(self, force):
        """download all packages for this version from the specified package source"""
        self.packages = [self.inst.server_package]
        if self.inst.client_package:
            self.packages.append(self.inst.client_package)
        if self.inst.debug_package:
            self.packages.append(self.inst.debug_package)

        for package in self.packages:
            self.funcs[self.source](self.directories[self.source], package, Path(self.options.package_dir), force)

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
# pylint: disable=too-many-arguments disable=unused-argument
def main(
        #very_common_options
        new_version, verbose, enterprise, package_dir, zip_package, hot_backup,
        # download options:
        enterprise_magic, force, source,
        httpuser, httppassvoid, remote_host):
# fmt: on
    """ main wrapper """
    dl_opts = DownloadOptions(force,
                              verbose,
                              Path(package_dir),
                              enterprise_magic,
                              httpuser,
                              httppassvoid,
                              remote_host)

    lh.configure_logging(verbose)
    downloader = Download(
        options=dl_opts,
        version=new_version,
        enterprise=enterprise,
        zip_package=zip_package,
        source=source)
    return downloader.get_packages(force)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter # fix clickiness.
    sys.exit(main())
