#!/usr/bin/env python3

""" Release testing script"""
import logging
from ftplib import FTP
from pathlib import Path
import sys
import click
from arangodb.installers import make_installer, InstallerConfig
import tools.loghelper as lh
import semver

import requests

logging.basicConfig(
    level=logging.INFO,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)



class acquire_package():
    def __init__(self,
                 version,
                 verbose,
                 package_dir,
                 enterprise,
                 enterprise_magic,
                 zip,
                 httpuser,
                 httppassvoid):
        """ main """
        lh.section("configuration")
        print("version: " + str(version))
        print("using enterpise: " + str(enterprise))
        print("using zip: " + str(zip))
        print("package directory: " + str(package_dir))
        print("verbose: " + str(verbose))
        self.user = httpuser
        self.passvoid = httppassvoid
    
        lh.section("startup")
        if verbose:
            logging.info("setting debug level to debug (verbose)")
            logging.getLogger().setLevel(logging.DEBUG)


        self.package_dir = Path(package_dir)
        self.cfg = InstallerConfig(version,
                                   verbose,
                                   enterprise,
                                   zip,
                                   self.package_dir,
                                   Path("/"),
                                   "",
                                   "127.0.0.1",
                                   False,
                                   False)
        self.inst = make_installer(self.cfg)

        is_nightly = self.inst.semver.prerelease == "nightly"
        self.params = {
            "full_version": 'v{major}.{minor}.{patch}'.format(**self.cfg.semver.to_dict()),
            "major_version": 'arangodb{major}{minor}'.format(**self.cfg.semver.to_dict()),
            "bare_major_version": '{major}.{minor}'.format(**self.cfg.semver.to_dict()),
            "remote_package_dir": self.inst.remote_package_dir,
            "enterprise": "Enterprise" if enterprise else "Community",
            "enterprise_magic": enterprise_magic + "/" if enterprise else "",
            "packages": "" if is_nightly else "packages",
            "nightly": "nightly" if is_nightly else ""
        }
        if is_nightly:
            self.params['enterprise'] = ""

        self.directories = {
            "ftp:stage1": '/buildfiles/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**self.params),
            "ftp:stage2": '/buildfiles/stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/'.format(**self.params),
            "http:stage1": 'stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**self.params),
            "http:stage2": 'stage2/{nightly}/{bare_major_version}/{packages}/{enterprise}/{remote_package_dir}/'.format(**self.params),
            "public": '{enterprise_magic}{major_version}/{enterprise}/{remote_package_dir}/'.format(**self.params)
        }
        self.funcs = {
            "http:stage1": self.acquire_stage1_http,
            "http:stage2": self.acquire_stage2_http,
            "ftp:stage1": self.acquire_stage1_ftp,
            "ftp:stage2": self.acquire_stage2_ftp,
            "public": self.acquire_live
        }

    def acquire_stage_ftp(self, directory, package, local_dir, force, stage):
        out = local_dir / package
        if out.exists() and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{
                "file": str(out)
            }))
            return
        # ftp = FTP('Nas02.arangodb.biz') # no DNS no cry...
        ftp = FTP('172.16.1.22')
        print(stage + ": " + ftp.login(user='anonymous', passwd='anonymous', acct='anonymous'))
        print(directory)
        print(stage + ": " + ftp.cwd(directory))
        ftp.set_pasv(True)
        with out.open(mode='wb') as fd:
            print(stage + ": downloading to " + str(out))
            print(stage + ": " + ftp.retrbinary('RETR ' + package, fd.write))
    
    def acquire_stage_http(self, directory, package, local_dir, force, stage):
        #url = 'https://{user}:{passvoid}@Nas02.arangodb.biz/{dir}{pkg}'.format(**{
        #    'passvoid': passvoid,
        #    'user': user,
        #    'dir': directory,
        #    'pkg': package
        #    })
    
        url = 'https://{user}:{passvoid}@fileserver.arangodb.com:8529/{dir}{pkg}'.format(**{
            'passvoid': self.passvoid,
            'user': self.user,
            'dir': directory,
            'pkg': package
            })
    
        out = local_dir / package
        if out.exists() and not force:
            print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{
                "file": str(out)
            }))
            return
        print(stage + ": downloading " + str(url))
        res = requests.get(url)
        if res.status_code == 200:
            print(stage + ": writing {size} kbytes to {file}".format(**{
                "size": str(len(res.content) / 1024),
                "file": str(out)
            }))
            out.write_bytes(res.content)
        else:
            raise Exception(stage + ": failed to download {url} - {error} - {msg}".format(**{
                "url": url,
                "error": res.status_code,
                "msg": res.text
                }))
    
    def acquire_stage1_http(self, directory, package, local_dir, force):
        self.acquire_stage_http(directory, package, local_dir, force, "STAGE_1_HTTP")
    
    def acquire_stage2_http(self, directory, package, local_dir, force):
        self.acquire_stage_http(directory, package, local_dir, force, "STAGE_2_HTTP")
    
    def acquire_stage1_ftp(self, directory, package, local_dir, force):
        self.acquire_stage_ftp(directory, package, local_dir, force, "STAGE_1_FTP")
    
    def acquire_stage2_ftp(self, directory, package, local_dir, force):
        self.acquire_stage_ftp(directory, package, local_dir, force, "STAGE_2_FTP")
    
    def acquire_live(self, directory, package, local_dir, force):
        print('live')
        url = 'https://download.arangodb.com/{dir}{pkg}'.format(**{
            'dir': directory,
            'pkg': package
            })
    
        out = local_dir / package
        if out.exists() and not force:
            print("LIVE: not overwriting {file} since not forced to overwrite!".format(**{
                "file": str(out)
            }))
            return
        print("LIVE: downloading " + str(url))
        res = requests.get(url)
        if res.status_code == 200:
            print("LIVE: writing {size} kbytes to {file}".format(**{
                "size": str(len(res.content) / 1024),
                "file": str(out)
            }))
            out.write_bytes(res.content)
        else:
            raise Exception("LIVE: failed to download {url} - {error} - {msg}".format(**{
                "url": url,
                "error": res.status_code,
                "msg": res.text
                }))
    def get_packages(self, force, source):
        self.packages = [
            self.inst.server_package
        ]
        if self.inst.client_package:
            self.packages.append(self.inst.client_package)
        if self.inst.debug_package:
            self.packages.append(self.inst.debug_package)
    
        for package in self.packages:
            self.funcs[source](self.directories[source], package, Path(self.package_dir), force)

    def get_version_info(self, source):
        sl = 'sourceInfo.log'
        self.funcs[source](self.directories[source], sl, Path(self.package_dir), True)
        return (self.package_dir / sl).read_text()

@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise/--no-enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--enterprise-magic',
              default='',
              help='Enterprise or community?')
@click.option('--zip/--no-zip',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to store the packages to.')
@click.option('--force/--no-force',
              is_flag=True,
              default=False,
              help='whether to overwrite existing target files or not.')
@click.option('--source',
              default='public',
              help='where to download the package from [[ftp|http]:stage1|[ftp|http]:stage2|public]')
@click.option('--httpuser',
              default="",
              help='user for external http download')
@click.option('--httppassvoid',
              default="",
              help='passvoid for external http download')

def main(version, verbose, package_dir, enterprise, enterprise_magic, zip, force, source, httpuser, httppassvoid):
    
    dl = acquire_package(version, verbose, package_dir, enterprise, enterprise_magic, zip, httpuser, httppassvoid)
    return dl.get_packages(force, source)

if __name__ == "__main__":
    sys.exit(main())
