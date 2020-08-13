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
    print('stage')
    print('directory: ' + directory)
    print('package: '+ package)
    out = local_dir / package
    if out.exists() and not force:
        print(stage + ": not overwriting {file} since not forced to overwrite!".format(**{
            "file": str(out)
        }))
        return
    ftp = FTP('Nas02.arangodb.biz')
    print(ftp.login(user='', passwd='', acct = ''))
    print(ftp.cwd(directory))
    print(ftp.set_pasv(True))
    with out.open() as fd:
        print(str(fd))
        print(package)
        print(ftp.retrbinary('STOR ' + package, fd))

def acquire_stage(directory, package, local_dir, force, stage):
    global passvoid, user
    url = 'https://{user}:{passvoid}@Nas02.arangodb.biz/{dir}{pkg}'.format(**{
        'passvoid': passvoid,
        'user': user,
        'dir': directory,
        'pkg': package
        })

    #url = 'https://{user}:{passvoid}@fileserver.arangodb.com:8529/{dir}{pkg}'.format(**{
    #    'passvoid': passvoid,
    #    'user': user,
    #    'dir': directory,
    #    'pkg': package
    #    })

    # https://fileserver.arangodb.com:8529
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

def acquire_stage1(directory, package, local_dir, force):
    acquire_stage(directory, package, local_dir, force, "STAGE_1")

def acquire_stage2(directory, package, local_dir, force):
    acquire_stage(directory, package, local_dir, force, "STAGE_2")

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
              help='where to download the package from [stage1|stage2|public]')

def acquire_package(version, verbose, package_dir, enterprise, enterprise_magic, zip, force, source):
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip))
    print("package directory: " + str(package_dir))
    print("verbose: " + str(verbose))

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    install_config = InstallerConfig(version,
                                     verbose,
                                     enterprise,
                                     zip,
                                     Path(package_dir),
                                     "",
                                     "127.0.0.1",
                                     False)
                             
    inst = make_installer(install_config)

    params = {
        "full_version": 'v3.7.1',
        "bare_major_version": '3.7',
        "major_version": 'arangodb37',
        "remote_package_dir": inst.remote_package_dir,
        "enterprise": "Enterprise" if enterprise else "Community",
        "enterprise_magic": enterprise_magic,
    }

    print(params)
    directories = {
        # ftp: "stage1": '/buildfiles/stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        # ftp: "stage2": '/buildfiles/stage2/{bare_major_version}/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "stage1": 'stage1/{full_version}/release/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "stage2": 'stage2/{bare_major_version}/packages/{enterprise}/{remote_package_dir}/'.format(**params),
        "public": '{enterprise_magic}/{major_version}/{enterprise}/{remote_package_dir}/'.format(**params)
    }

    funcs = {
        "stage1": acquire_stage1,
        "stage2": acquire_stage2,
        "public": acquire_live
    }
    
    
    print(directories)
    packages = [
      #   inst.server_package
    ]
    if hasattr(inst, 'client_package'):
        packages.append(inst.client_package)
#    if hasattr(inst, 'debug_package'):
#        packages.append(inst.debug_package)

    for package in packages:
        funcs[source](directories[source], package, Path(package_dir), force)
    
if __name__ == "__main__":
    sys.exit(acquire_package())
