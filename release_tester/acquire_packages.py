#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import sys
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner
import tools.loghelper as lh

import requests
from ftplib import FTP

logging.basicConfig(
    level=logging.INFO,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)

passvoid = ''
user = ''

def acquire_stage_ftp(directory, package, local_dir, force, stage):
    out = local_dir / package
    if out.exists() and not force:
        print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{
            "file": str(out)
        }))
        return
    ftp = FTP('Nas02.arangodb.biz')
    print(stage + ": " + ftp.login(user='anonymous', passwd='anonymous', acct = 'anonymous'))
    print(stage + ": " + ftp.cwd(directory))
    ftp.set_pasv(True)
    with out.open(mode='wb') as fd:
        print(stage + ": downloading to " + str(out))
        print(stage + ": " + ftp.retrbinary('RETR ' + package, fd.write))

def acquire_stage_http(directory, package, local_dir, force, stage):
    global passvoid, user
    #url = 'https://{user}:{passvoid}@Nas02.arangodb.biz/{dir}{pkg}'.format(**{
    #    'passvoid': passvoid,
    #    'user': user,
    #    'dir': directory,
    #    'pkg': package
    #    })

    url = 'https://{user}:{passvoid}@fileserver.arangodb.com:8529/{dir}{pkg}'.format(**{
        'passvoid': passvoid,
        'user': user,
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

def acquire_stage1_http(directory, package, local_dir, force):
    acquire_stage_http(directory, package, local_dir, force, "STAGE_1_HTTP")

def acquire_stage2_http(directory, package, local_dir, force):
    acquire_stage_http(directory, package, local_dir, force, "STAGE_2_HTTP")

def acquire_stage1_ftp(directory, package, local_dir, force):
    acquire_stage_ftp(directory, package, local_dir, force, "STAGE_1_FTP")

def acquire_stage2_ftp(directory, package, local_dir, force):
    acquire_stage_ftp(directory, package, local_dir, force, "STAGE_2_FTP")

def acquire_live(directory, package, local_dir, force):    
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
    
@click.command()
@click.option('--version', help='ArangoDB version number.')
@click.option('--verbose/--no-verbose',
              is_flag=True,
              default=False,
              help='switch starter to verbose logging mode.')
@click.option('--enterprise',
              is_flag=True,
              default=False,
              help='Enterprise or community?')
@click.option('--enterprise-magic',
              default='',
              help='Enterprise or community?')
@click.option('--zip',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to store the packages to.')
@click.option('--force',
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

def acquire_package(version, verbose, package_dir, enterprise, enterprise_magic, zip, force, source, httpuser, httppassvoid):
    global passvoid, user
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip))
    print("package directory: " + str(package_dir))
    print("verbose: " + str(verbose))
    user = httpuser
    passvoid = httppassvoid

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    cfg = InstallerConfig(version,
                          verbose,
                          enterprise,
                          zip,
                          Path(package_dir),
                          "",
                          "127.0.0.1",
                          False)
                             
    inst = make_installer(cfg)

    params = {
        "full_version": 'v{major}.{minor}.{patch}'.format(**cfg.semver.to_dict()),
        "major_version": 'arangodb{major}{minor}'.format(**cfg.semver.to_dict()),
        "bare_major_version": '{major}.{minor}'.format(**cfg.semver.to_dict()),
        "remote_package_dir": inst.remote_package_dir,
        "enterprise": "Enterprise" if enterprise else "Community",
        "enterprise_magic": enterprise_magic,
    }

    print(params)
    directories = {
        "ftp:stage1": '/buildfiles/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "ftp:stage2": '/buildfiles/stage2/{bare_major_version}/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "http:stage1": 'stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "http:stage2": 'stage2/{bare_major_version}/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "public": '{enterprise_magic}/{major_version}/{enterprise}/{remote_package_dir}/'.format(**params)
    }

    funcs = {
        "http:stage1": acquire_stage1_http,
        "http:stage2": acquire_stage2_http,
        "ftp:stage1": acquire_stage1_ftp,
        "ftp:stage2": acquire_stage2_ftp,
        "public": acquire_live
    }
    
    
    print(directories)
    packages = [
        inst.server_package
    ]
    if inst.client_package:
        packages.append(inst.client_package)
    if inst.debug_package:
        packages.append(inst.debug_package)

    for package in packages:
        funcs[source](directories[source], package, Path(package_dir), force)
    
if __name__ == "__main__":
    sys.exit(acquire_package())
