#!/usr/bin/env python
""" Manage one instance of the arangodb hotbackup CLI tool """

import logging
import json
import re
import time
import copy
from os import environ

from reporting.reporting_utils import step

from tools.asciiprint import ascii_convert_str, print_progress as progress
import tools.loghelper as lh

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor
from arangodb.installers import HotBackupMode, HotBackupProviders

HB_2_RCLONE_TYPE = {
    HotBackupMode.DISABLED: "disabled",
    HotBackupMode.DIRECTORY: "local",
    HotBackupMode.S3BUCKET: "S3",
}

HB_2_RCLONE_PROVIDER_DEFAULT = {
    HotBackupMode.DISABLED: None,
    HotBackupMode.DIRECTORY: None,
    HotBackupMode.S3BUCKET: HotBackupProviders.MINIO,
}

ALLOWED_PROVIDERS = {
    HotBackupMode.DISABLED: [],
    HotBackupMode.DIRECTORY: [],
    HotBackupMode.S3BUCKET: [HotBackupProviders.MINIO, HotBackupProviders.AWS],
}


class HotBackupConfig:
    """manage rclone setup"""

    def __init__(self, basecfg, name, raw_install_prefix):
        self.cfg = basecfg
        self.install_prefix = raw_install_prefix
        self.cfg_type = HB_2_RCLONE_TYPE[basecfg.hb_mode]
        self.name = str(name).replace("/", "_").replace(".", "_")
        if not basecfg.hb_provider:
            self.provider = HB_2_RCLONE_PROVIDER_DEFAULT[basecfg.hb_mode]
        elif basecfg.hb_provider not in ALLOWED_PROVIDERS[basecfg.hb_mode]:
            raise Exception(
                f"Storage provider {basecfg.hb_provider} is not allowed for rclone config type {basecfg.hb_mode}!"
            )
        else:
            self.provider = basecfg.hb_provider
        self.acl = "private"
        config = {}
        config["type"] = self.cfg_type

        if basecfg.hb_mode == HotBackupMode.S3BUCKET and self.provider == HotBackupProviders.MINIO:
            self.name = "S3"
            config["type"] = "s3"
            config["provider"] = "minio"
            config["env_auth"] = "false"
            config["access_key_id"] = "minio"
            config["secret_access_key"] = "minio123"
            config["endpoint"] = "http://minio1:9000"
            config["region"] = "us-east-1"
        elif basecfg.hb_mode == HotBackupMode.S3BUCKET and self.provider == HotBackupProviders.AWS:
            try:
                self.name = "S3"
                config["type"] = "s3"
                config["provider"] = "AWS"
                config["env_auth"] = "false"
                config["access_key_id"] = environ["AWS_ACCESS_KEY_ID"]
                config["secret_access_key"] = environ["AWS_SECRET_ACCESS_KEY"]
                config["region"] = environ["AWS_REGION"]
                config["acl"] = environ["AWS_ACL"]
            except KeyError as exc:
                raise Exception(
                    "Please set AWS credentials as environment variables AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_ACL"
                ) from exc
        elif basecfg.hb_mode == HotBackupMode.DIRECTORY:
            config["copy-links"] = "false"
            config["links"] = "false"
            config["one_file_system"] = "true"
        self.config = {self.name: config}

        self.hb_storage_path_prefix = basecfg.hb_storage_path_prefix
        self.remote_storage_path_prefix = f"{self.name}:/{self.hb_storage_path_prefix}"
        while "//" in self.remote_storage_path_prefix:
            self.remote_storage_path_prefix = self.remote_storage_path_prefix.replace("//", "/")

    def save_config(self, filename):
        """writes a hotbackup rclone configuration file"""
        fhandle = self.install_prefix / filename
        print(json.dumps(self.config))
        fhandle.write_text(json.dumps(self.config))
        return str(fhandle)

    def get_rclone_config_file(self):
        """create a config file and return its full name"""
        return self.save_config("rclone_config.json")

    def construct_remote_storage_path(self, postfix):
        result = self.remote_storage_path_prefix + "/" + postfix
        while "//" in result:
            result = result.replace("//", "/")
        return result


class HotBackupManager(ArangoCLIprogressiveTimeoutExecutor):
    # pylint: disable=too-many-instance-attributes
    """manages one arangobackup instance"""

    def __init__(self, config, name, raw_install_prefix, connect_instance):
        super().__init__(config, connect_instance)

        # directories
        self.name = str(name)
        self.install_prefix = raw_install_prefix
        self.basedir = raw_install_prefix

        self.backup_dir = self.install_prefix / "backup"
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)

    @step
    def run_backup(self, arguments, name, silent=False, expect_to_fail=False):
        """run arangobackup"""
        if not silent:
            logging.info("running hot backup " + name)
        run_cmd = copy.deepcopy(self.cfg.default_backup_args)
        if self.cfg.verbose:
            run_cmd += ["--log.level=debug"]
        run_cmd += arguments
        lh.log_cmd(arguments, not silent)

        def inspect_line_result(line):
            strline = str(line)
            if strline.find("ERROR") >= 0:
                return True
            return False

        success, output, _, error_found = self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangobackup",
            run_cmd,
            20,
            inspect_line_result,
            self.cfg.verbose and not silent,
            expect_to_fail,
        )

        if not success:
            raise Exception("arangobackup exited " + str(output))

        if not success or error_found:
            raise Exception("arangobackup indicated 'ERROR' in its output: %s" % ascii_convert_str(output))
        return output

    @step
    def create(self, backup_name):
        """create a hot backup"""
        args = ["create", "--label", backup_name, "--max-wait-for-lock", "180"]
        out = self.run_backup(args, backup_name)
        for line in out.split("\n"):
            match = re.match(r".*identifier '(.*)'", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of backup!")

    def list(self):
        """list available hot backups"""
        args = ["list"]
        out = self.run_backup(args, "list")
        backups = []
        for line in out.split("\n"):
            match = re.match(r".* - (.*)$", line)
            if match:
                backups.append(match.group(1))
        return backups

    @step
    def restore(self, backup_name):
        """restore an existing hot backup"""
        args = ["restore", "--identifier", backup_name]
        self.run_backup(args, backup_name)

    @step
    def delete(self, backup_name):
        """delete an existing hot backup"""
        args = ["delete", "--identifier", backup_name]
        self.run_backup(args, backup_name)

    @step
    def upload(self, backup_name, backup_config: HotBackupConfig, identifier):
        """upload a backup using rclone on the server"""
        # fmt: off
        args = [
            'upload',
            '--label', identifier,
            '--identifier', backup_name,
            '--rclone-config-file', backup_config.get_rclone_config_file(),
            '--remote-path', backup_config.construct_remote_storage_path(str(self.backup_dir))
        ]
        # fmt: on
        out = self.run_backup(args, backup_name)
        for line in out.split("\n"):
            match = re.match(r".*arangobackup upload --status-id=(\d*)", str(line))
            if match:
                # time.sleep(600000000)
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")

    def upload_status(self, backup_name: str, status_id: str, instance_count: int, timeout: int = 180):
        """checking the progress of up/download"""
        args = [
            "upload",
            "--status-id",
            status_id,
        ]
        while True:
            out = self.run_backup(args, backup_name, True)
            progress(".")
            counts = {
                "ACK": 0,
                "STARTED": 0,
                "COMPLETED": 0,
                "FAILED": 0,
                "CANCELLED": 0,
            }
            for line in out.split("\n"):
                match = re.match(r".*Status: (.*)", str(line))
                if match:
                    which = match.group(1)
                    try:
                        counts[which] += 1
                    except AttributeError:
                        print("Line with unknown status [%s]: %s %s" % (which, line, str(counts)))

            if counts["COMPLETED"] == instance_count:
                print("all nodes have completed to restore the backup")
                return
            if counts["FAILED"] > 0:
                raise Exception("failed to create backup: " + str(out))
            print("have to retry. " + str(counts) + " - " + str(instance_count))
            timeout -= 1
            if timeout <= 0:
                raise TimeoutError("failed to find %d 'COMPLETED' status for upload status" % instance_count)
            time.sleep(1)

    @step
    def download(self, backup_name, backup_config: HotBackupConfig, identifier):
        """download a backup using rclone on the server"""
        # fmt: off
        args = [
            'download',
            '--label', identifier,
            '--identifier', backup_name,
            '--rclone-config-file', backup_config.get_rclone_config_file(),
            '--remote-path', backup_config.construct_remote_storage_path(str(self.backup_dir))
        ]
        # fmt: on
        out = self.run_backup(args, backup_name)
        for line in out.split("\n"):
            match = re.match(r".*arangobackup download --status-id=(\d*)", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")
