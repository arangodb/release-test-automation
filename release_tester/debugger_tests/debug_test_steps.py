#!/usr/bin/env python3
"""test steps for dubug symbols"""
import os
import re
import shutil
import subprocess
from pathlib import Path

import psutil
from allure_commons._allure import attach

import tools.loghelper as lh
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from reporting.reporting_utils import step

# pylint: disable=broad-except
from tools.clihelper import run_cmd_and_log_stdout
from tools.killall import kill_all_processes


@step
def create_arangod_dump(installer, starter_dir: str, dump_file_dir: str):
    """create arangod memory dump file"""
    starter = StarterManager(
        basecfg=installer.cfg,
        install_prefix=Path(starter_dir),
        instance_prefix="single",
        expect_instances=[InstanceType.SINGLE],
        mode="single",
        jwt_str="single",
    )
    dump_filename = None
    try:
        with step("Start a single server deployment"):
            starter.run_starter()
            starter.detect_instances()
            starter.detect_instance_pids()
            starter.set_passvoid("")
            pid = starter.all_instances[0].pid
        with step("Create a dump of arangod process"):
            cmd = ["procdump", "-ma", str(pid), dump_file_dir]
            lh.log_cmd(cmd)
            with psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                (procdump_out, procdump_err) = proc.communicate()
                procdump_str = str(procdump_out, "UTF-8")
                attach(procdump_str, "procdump sdtout")
                attach(str(procdump_err), "procdump stderr")
                success_string = "Dump 1 complete"
                filename_regex = re.compile(
                    r"^(\[\d{2}:\d{2}:\d{2}\] Dump 1 initiated: )(?P<filename>.*)$", re.MULTILINE
                )
                match = re.search(filename_regex, procdump_str)
                if procdump_str.find(success_string) < 0 or not match:
                    raise Exception("procdump wasn't able to create a dump file: " + procdump_str)
                dump_filename = match.group("filename")
    finally:
        starter.terminate_instance()
        kill_all_processes()
    return dump_filename


@step
def create_arangosh_dump(installer, dump_file_dir: str):
    """create arangosh memory dump file"""
    dump_filename = None
    with step("Start arangosh process"):
        exe_file = installer.cfg.bin_dir / "arangosh.exe"
        cmd = [str(exe_file)]
        arangosh_proc = psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        arangosh_pid = arangosh_proc.pid
    with step("Create a dump of arangosh process"):
        cmd = ["procdump", "-ma", str(arangosh_pid), dump_file_dir]
        lh.log_cmd(cmd)
        with psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            (procdump_out, procdump_err) = proc.communicate()
            procdump_str = str(procdump_out, "UTF-8")
            attach(procdump_str, "procdump sdtout")
            attach(str(procdump_err), "procdump stderr")
            success_string = "Dump 1 complete"
            filename_regex = re.compile(r"^(\[\d{2}:\d{2}:\d{2}\] Dump 1 initiated: )(?P<filename>.*)$", re.MULTILINE)
            match = re.search(filename_regex, procdump_str)
            if procdump_str.find(success_string) < 0 or not match:
                raise Exception("procdump wasn't able to create a dump file: " + procdump_str)
            dump_filename = match.group("filename")
    with step("Kill arangosh process"):
        arangosh_proc.kill()
    return dump_filename


def create_dump_for_exe(exe_file: str, dump_file_dir: str):
    """run given executable and create a memory dump at any point of execution"""
    exe_file = Path(exe_file)
    exe_name = exe_file.name
    with step(f"Create a memory dump of the program: {exe_name}"):
        dump_filename = None
        cmd = ["procdump", "-ma", "-t", "-x", dump_file_dir, str(exe_file)]
        lh.log_cmd(cmd)
        with psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            (procdump_out, procdump_err) = proc.communicate()
            procdump_str = str(procdump_out, "UTF-8")
            attach(procdump_str, "procdump sdtout")
            attach(str(procdump_err), "procdump stderr")
            success_string = "Dump 1 complete"
            filename_regex = re.compile(r"^(\[\d{2}:\d{2}:\d{2}\] Dump 1 initiated: )(?P<filename>.*)$", re.MULTILINE)
            match = re.search(filename_regex, procdump_str)
            if procdump_str.find(success_string) < 0 or not match:
                raise Exception("procdump wasn't able to create a dump file: " + procdump_str)
            dump_filename = match.group("filename")
        return dump_filename


def store(pdb_filename: str, target_dir: str):
    """store pdb file in symbol server directory"""
    with step(f"Store pdb file {pdb_filename} in symbol server directory"):
        print(f"Storing file {pdb_filename}")
        command = ["symstore.exe", "add", "/f", pdb_filename, "/s", target_dir, "/t", "ArangoDB", "/compress"]
        run_cmd_and_log_stdout(command)
        print(f"File {pdb_filename} successfully stored to {target_dir}")


@step
def store_all_files_in_dir(
    source_directory: str, target_directory: str, clean_dir: bool = False, create_dir: bool = True
):
    """Add PDB files to a symbol server directory"""
    if os.path.exists(target_directory) and not os.path.isdir(target_directory):
        raise Exception(f"Path {target_directory} is not a directory")
    if clean_dir and os.path.isdir(target_directory):
        shutil.rmtree(target_directory)
        Path(target_directory).mkdir(parents=True)
    if create_dir and not os.path.isdir(target_directory):
        Path(target_directory).mkdir(parents=True)
    for filename in os.listdir(source_directory):
        path = os.path.join(source_directory, filename)
        if os.path.isfile(path):
            store(str(path), target_directory)
