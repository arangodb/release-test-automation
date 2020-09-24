#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import sys
import click
import re
from tools.killall import kill_all_processes
from arangodb.installers import make_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner
import tools.loghelper as lh

logging.basicConfig(
    level=logging.INFO,
    datefmt='%H:%M:%S',
    format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d - %(message)s'
)


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
@click.option('--zip/--no-zip',
              is_flag=True,
              default=False,
              help='switch to zip or tar.gz package instead of default OS package')
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=False,
              help='wait for the user to hit Enter?')
@click.option('--package-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--mode',
              default='all',
              help='operation mode - [all|install|uninstall|tests].')
@click.option('--starter-mode',
              default='all',
              help='which starter deployments modes to use - ' +
              '[all|LF|AFO|CL|DC|none].')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')

@click.option('--frontends',
              multiple=True,
              help='Connection strings of remote clusters')


def run_test(version, verbose, package_dir, enterprise, zip,
             interactive, mode, starter_mode, publicip, frontends):
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " + str(zip))
    print("package directory: " + str(package_dir))
    print("mode: " + str(mode))
    print("starter mode: " + str(starter_mode))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    if mode not in ['all', 'install', 'system', 'tests', 'uninstall']:
        raise Exception("unsupported mode %s!" % mode)

    do_install = mode == "all" or mode == "install"
    do_uninstall = mode == "all" or mode == "uninstall"

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    install_config = InstallerConfig(version,
                                     verbose,
                                     enterprise,
                                     zip,
                                     Path(package_dir),
                                     mode,
                                     publicip,
                                     interactive)

    split_host = re.compile(r'([a-z]*)://([0-9.:]*):(\d*)')

    inst = make_installer(install_config)


    from arangodb.starter.deployments.cluster_perf import ClusterPerf
    from arangodb.starter.deployments import RunnerType
    if len(frontends) > 0:
        for frontend in frontends:
            print('remote')
            h = re.split(split_host, frontend)
            inst.cfg.add_frontend(h[1], h[2], h[3])
    print(len(inst.cfg.frontends))
    runner = ClusterPerf(RunnerType.CLUSTER, inst.cfg, inst, None, None)
    runner.do_install = do_install
    runner.do_uninstall = do_uninstall
    failed = False
    if not runner.run():
        failed = True

    if len(frontends) == 0:
        kill_all_processes()

    return ( 0 if not failed else 1 )


if __name__ == "__main__":
    sys.exit(run_test())
