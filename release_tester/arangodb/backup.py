#!/usr/bin/env python
""" Manage one instance of the arangodb hotbackup CLI tool """

import logging
import json
import re
import subprocess
import time

import psutil

from tools.asciiprint import ascii_convert, ascii_print, print_progress as progress
import tools.loghelper as lh

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

class HotBackupManager():
    # pylint: disable=R0902
    """ manages one arangobackup instance"""
    def __init__(self,
                 basecfg,
                 name,
                 raw_install_prefix):

        self.cfg = basecfg
        self.moreopts = [
            '--server.endpoint', "tcp://127.0.0.1:{cfg.port}".format(cfg=self.cfg),
            '--server.username', str(self.cfg.username),
            '--server.password', str(self.cfg.passvoid),
            # else the wintendo may stay mute:
            '--log.force-direct', 'true', '--log.foreground-tty', 'true'
        ]
        if self.cfg.verbose:
            self.moreopts += ["--log.level=debug"]

        #directories
        self.name = str(name)
        self.install_prefix = raw_install_prefix
        self.basedir = raw_install_prefix

        self.username = 'testuser'
        self.passvoid = 'testpassvoid'
        self.backup_dir = self.install_prefix / 'backup'
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

    def set_passvoid(self, passvoid):
        """ replace the passvoid """
        self.cfg.passvoid = passvoid
        self.moreopts += [
            '--server.password', str(self.cfg.passvoid),
        ]

    def run_backup(self, arguments, name, silent=False):
        """ launch the starter for this instance"""
        if not silent:
            logging.info("running hot backup " + name)
        args = [self.cfg.bin_dir / 'arangobackup'] + arguments + self.moreopts
        if not silent:
            lh.log_cmd(args)
        instance = psutil.Popen(args,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        (output, err) = instance.communicate()
        if len(err) > 0:
            ascii_print(str(err))
        success = True
        if not silent:
            for line in output.splitlines():
                strline = str(line)
                ascii_print(strline)
                if strline.find('ERROR') >= 0:
                    success = False
        instance.wait()
        if instance.returncode != 0:
            raise Exception("arangobackup exited " + str(instance.returncode))
        if not success:
            raise Exception("arangobackup indicated 'ERROR' in its output: %s" %
                            ascii_convert(output))
        return output.splitlines()

    def create(self, backup_name):
        """ create a hot backup """
        args = ['create', '--label', backup_name, '--max-wait-for-lock', '180']
        out = self.run_backup(args, backup_name)
        for line in out:
            match = re.match(r".*identifier '(.*)'", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of backup!")

    def list(self):
        """ list available hot backups """
        args = ['list']
        out = self.run_backup(args, "list")
        backups = []
        for line in out:
            match = re.match(r".* - (.*)'$", str(line))
            if match:
                backups.append(match.group(1))
        return backups

    def restore(self, backup_name):
        """ restore an existing hot backup """
        args = ['restore', '--identifier', backup_name]
        self.run_backup(args, backup_name)

    def delete(self, backup_name):
        """ delete an existing hot backup """
        args = ['delete', '--identifier', backup_name]
        self.run_backup(args, backup_name)

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
        for line in out:
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
            for line in out:
                match = re.match(r".*Status: (.*)'", str(line))
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
        for line in out:
            match = re.match(r".*arangobackup download --status-id=(\d*)", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")
