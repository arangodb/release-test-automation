#!/usr/bin/env python3

#!/usr/bin/env python3

""" Release testing script"""
import logging
from pathlib import Path
import sys
from threading  import Thread
import click
from tools.killall import kill_all_processes
from arangodb.installers import make_source_installer, InstallerConfig
from arangodb.starter.deployments import RunnerType, make_runner
import tools.loghelper as lh
from arangodb.sh import ArangoshExecutor
from queue import Queue, Empty
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
@click.option('--interactive/--no-interactive',
              is_flag=True,
              default=sys.stdout.isatty(),
              help='wait for the user to hit Enter?')
@click.option('--source-dir',
              default='/tmp/',
              help='directory to load the packages from.')
@click.option('--build-dir', default='build',
              help='where the files are built')
@click.option('--publicip',
              default='127.0.0.1',
              help='IP for the click to browser hints.')


def run_test(version, verbose, source_dir, build_dir, enterprise,
             interactive, publicip):
    """ main """
    lh.section("configuration")
    print("version: " + str(version))
    print("using enterpise: " + str(enterprise))
    print("using zip: " +   str(zip))
    print("source directory: " + str(source_dir))
    print("build directory" + str(build_dir))
    print("public ip: " + str(publicip))
    print("interactive: " + str(interactive))
    print("verbose: " + str(verbose))

    lh.section("startup")
    if verbose:
        logging.info("setting debug level to debug (verbose)")
        logging.getLogger().setLevel(logging.DEBUG)

    install_config = InstallerConfig(version,
                                     verbose,
                                     enterprise,
                                     False,
                                     Path(source_dir),
                                     build_dir,
                                     publicip,
                                     interactive)

    inst = make_source_installer(install_config)

    q = Queue()
    jobs = [
          ['1/8'],
          ['2/8'],
          ['3/8'],
          ['4/8'],
          ['5/8']
    ]
    for job in jobs:
        q.put(job)

    testcount = q.qsize()
    threads = [
        Thread(target=run_tests, args=(q, inst.cfg)),
        Thread(target=run_tests, args=(q, inst.cfg))
    ]

    for thread in threads:
        thread.start()
    #run_tests(q, inst.cfg)
    for thread in threads:
        thread.join()


    failed = False
    return ( 0 if not failed else 1 )

def run_tests(q, cfg):
    sh = ArangoshExecutor(cfg)

    job = q.get()
    while job:
        sh.run_testing('shell_client', job, 1000, Path('/tmp/bla.log'))
        job = q.get()
        
if __name__ == "__main__":
    sys.exit(run_test())
