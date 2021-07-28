#!/usr/bin/env python
""" Manage one instance of the arangodb hotbackup CLI tool """

import logging
import json
import re
import time

from reporting.reporting_utils import step
import psutil

from tools.asciiprint import ascii_convert, print_progress as progress
import tools.loghelper as lh

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor

#            json.dumps({
#                self.name: {
#                    "type": self.cfg_type,
#                    "ftp-host": "127.0.0.1",
#                    "ftp-user": "testftp",
#                    "ftp-pass": "testpassvoid"
#                }
#            })

class HotBackupConfig():
    """ manage rclone setup """
    def __init__(self,
                 basecfg,
                 name,
                 raw_install_prefix):
        self.cfg = basecfg
        self.install_prefix = raw_install_prefix
        self.cfg_type = "local"
        self.name = str(name).replace('/', '_')
        #self.provider = None
        #self.env_auth = False
        #self.access_key_id = None
        #self.secret_access_key = None
        #self.region = None
        self.acl = "private"

    def save_config(self, filename):
        """ writes a hotbackup rclone configuration file """
        fhandle = self.install_prefix / filename
        fhandle.write_text(
            json.dumps({
                self.name: {
                    "type": self.cfg_type,
                    "copy-links": "false",
                    "links": "false",
                    "one_file_system": "true"
                }
            })
        )
        return str(fhandle)

    def get_rclone_config_file(self):
        """ create a config file and return its full name """
        return self.save_config("rclone_config.json")

class HotBackupManager(ArangoCLIprogressiveTimeoutExecutor):
    # pylint: disable=R0902
    """ manages one arangobackup instance"""
    def __init__(self,
                 config,
                 name,
                 raw_install_prefix,
                 connect_instance):
        super().__init__(config, connect_instance)

        #directories
        self.name = str(name)
        self.install_prefix = raw_install_prefix
        self.basedir = raw_install_prefix

        self.backup_dir = self.install_prefix / 'backup'
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

    @step("Run backup")
    def run_backup(self, arguments, name, silent=False):
        """ launch the starter for this instance"""
        if not silent:
            logging.info("running hot backup " + name)
        run_cmd = []
        if self.cfg.verbose:
            run_cmd += ["--log.level=debug"]
        run_cmd += arguments
        if not silent:
            lh.log_cmd(arguments)

        def inspect_line_result(line):
            strline = str(line)
            if strline.find('ERROR') >= 0:
                return True
            return False

        success, output, _, error_found = self.run_arango_tool_monitored(
            self.cfg.bin_dir / 'arangobackup',
            run_cmd,
            20,
            inspect_line_result,
            self.cfg.verbose and not silent)

        if not success:
            raise Exception("arangobackup exited " + str(output))

        if not success or error_found:
            raise Exception("arangobackup indicated 'ERROR' in its output: %s" %
                            ascii_convert(output))
        return output

    @step("Create a hot backup")
    def create(self, backup_name):
        """ create a hot backup """
        args = ['create', '--label', backup_name, '--max-wait-for-lock', '180']
        out = self.run_backup(args, backup_name)
        for line in out.split('\n'):
            match = re.match(r".*identifier '(.*)'", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of backup!")

    def list(self):
        """ list available hot backups """
        args = ['list']
        out = self.run_backup(args, "list")
        backups = []
        for line in out.split('\n'):
            match = re.match(r".* - (.*)$", line)
            if match:
                backups.append(match.group(1))
        return backups

    @step("Restore an existing hot backup")
    def restore(self, backup_name):
        """ restore an existing hot backup """
        args = ['restore', '--identifier', backup_name]
        self.run_backup(args, backup_name)

    @step("Delete an existing hot backup")
    def delete(self, backup_name):
        """ delete an existing hot backup """
        args = ['delete', '--identifier', backup_name]
        self.run_backup(args, backup_name)

    @step("Upload a backup using rclone")
    def upload(self, backup_name, backup_config: HotBackupConfig, identifier):
        """ upload a backup using rclone on the server """
        args = [
            'upload',
            '--label', identifier,
            '--identifier', backup_name,
            '--rclone-config-file', backup_config.get_rclone_config_file(),
            '--remote-path', backup_config.name + '://' + str(self.backup_dir)
        ]
        out = self.run_backup(args, backup_name)
        for line in out.split('\n'):
            match = re.match(r".*arangobackup upload --status-id=(\d*)", str(line))
            if match:
                # time.sleep(600000000)
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")

    def upload_status(self,
                      backup_name: str,
                      status_id: str,
                      instance_count: int,
                      timeout: int = 180):
        """ checking the progress of up/download """
        args = [
            'upload',
            '--status-id', status_id,
        ]
        while True:
            out = self.run_backup(args, backup_name, True)
            progress('.')
            counts = {
                'ACK': 0,
                'STARTED': 0,
                'COMPLETED': 0,
                'FAILED': 0,
                'CANCELLED': 0
            }
            for line in out.split('\n'):
                match = re.match(r".*Status: (.*)", str(line))
                if match:
                    which = match.group(1)
                    try:
                        counts[which] += 1
                    except AttributeError:
                        print("Line with unknown status [%s]: %s %s"
                              %(which, line, str(counts)))

            if counts['COMPLETED'] == instance_count:
                return
            if counts['FAILED'] > 0:
                raise Exception("failed to create backup: " + str(out))
            print("have to retry. " + str(counts) + " - " + str(instance_count))
            timeout -= 1
            if timeout <= 0:
                raise TimeoutError(
                    "failed to find %d 'COMPLETED' status for upload status" %
                    instance_count)
            time.sleep(1)

    @step("Download a backup using rclone")
    def download(self, backup_name, backup_config: HotBackupConfig, identifier):
        """ download a backup using rclone on the server """
        args = [
            'download',
            '--label', identifier,
            '--identifier', backup_name,
            '--rclone-config-file', backup_config.get_rclone_config_file(),
            '--remote-path', backup_config.name + '://' + str(self.backup_dir)
        ]
        out = self.run_backup(args, backup_name)
        for line in out.split('\n'):
            match = re.match(r".*arangobackup download --status-id=(\d*)", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")
