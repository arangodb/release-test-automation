#!/usr/bin/env python
""" Manage one instance of the arangodb hotbackup CLI tool """

import logging
import json
import re
import time
import copy

from allure_commons._allure import attach

from reporting.reporting_utils import step

from tools.asciiprint import ascii_convert_str, print_progress as progress
import tools.loghelper as lh

from arangodb.async_client import ArangoCLIprogressiveTimeoutExecutor
from arangodb.installers import HotBackupMode, HotBackupProviders

HB_2_RCLONE_TYPE = {
    HotBackupMode.DISABLED: "disabled",
    HotBackupMode.DIRECTORY: "local",
    HotBackupMode.S3BUCKET: "s3",
    HotBackupMode.GCS: "google cloud storage",
    HotBackupMode.AZUREBLOBSTORAGE: "azureblob",
}

class HotBackupConfig:
    """manage rclone setup"""

    #values inside this list must be lower case
    SECRET_PARAMETERS = ["access_key_id", "secret_access_key", "service_account_credentials"]

    def __init__(self, basecfg, name, raw_install_prefix):
        self.hb_timeout = 20
        hbcfg = basecfg.hb_cli_cfg
        self.hb_provider_cfg = basecfg.hb_provider_cfg

        self.install_prefix = raw_install_prefix
        self.cfg_type = HB_2_RCLONE_TYPE[self.hb_provider_cfg.mode]
        self.name = str(name).replace("/", "_").replace(".", "_")
        config = {}
        config["type"] = self.cfg_type

        if (
            self.hb_provider_cfg.mode == HotBackupMode.S3BUCKET
            and self.hb_provider_cfg.provider == HotBackupProviders.MINIO
        ):
            self.name = "S3"
            config["type"] = HB_2_RCLONE_TYPE[self.hb_provider_cfg.mode]
            config["provider"] = "minio"
            config["env_auth"] = "false"
            config["access_key_id"] = "minio"
            config["secret_access_key"] = "minio123"
            config["endpoint"] = "http://minio1:9000"
            config["region"] = "us-east-1"
        elif (
            self.hb_provider_cfg.mode == HotBackupMode.S3BUCKET
            and self.hb_provider_cfg.provider == HotBackupProviders.AWS
        ):
            self.name = "S3"
            self.hb_timeout = 120
            config["type"] = HB_2_RCLONE_TYPE[self.hb_provider_cfg.mode]
            config["provider"] = "AWS"
            config["env_auth"] = "false"
            config["access_key_id"] = hbcfg.hb_aws_access_key_id
            config["secret_access_key"] = hbcfg.hb_aws_secret_access_key
            config["region"] = hbcfg.hb_aws_region
            config["acl"] = hbcfg.hb_aws_acl
        elif self.hb_provider_cfg.mode == HotBackupMode.DIRECTORY:
            config["copy-links"] = "false"
            config["links"] = "false"
            config["one_file_system"] = "true"
        elif self.hb_provider_cfg.mode == HotBackupMode.GCS and self.hb_provider_cfg.provider == HotBackupProviders.GCE:
            self.name = "GCE"
            self.hb_timeout = 240
            config["type"] = HB_2_RCLONE_TYPE[self.hb_provider_cfg.mode]
            config["project_number"] = hbcfg.hb_gce_project_number
            if hbcfg.hb_gce_service_account_credentials:
                config["service_account_credentials"] = hbcfg.hb_gce_service_account_credentials
            elif hbcfg.hb_gce_service_account_file:
                config["service_account_file"] = hbcfg.hb_gce_service_account_file
            else:
                raise Exception("Either \"service_account_credentials\" or \"service_account_file\" parameter must be specified for Google Cloud Storage.")
        elif self.hb_provider_cfg.mode == HotBackupMode.AZUREBLOBSTORAGE and self.hb_provider_cfg.provider == HotBackupProviders.AZURE:
            self.name = "azure"
            self.hb_timeout = 240
            config["type"] = HB_2_RCLONE_TYPE[self.hb_provider_cfg.mode]
            config["account"] = hbcfg.hb_azure_account
            config["key"] = hbcfg.hb_azure_key
        self.config = {self.name: config}

    def get_config_json(self):
        """json serializer"""
        return json.dumps(self.config)

    def get_config_json_sanitized(self):
        """json serializer"""
        cfg_copy = copy.deepcopy(self.config)
        for cfg_name in cfg_copy:
            for param_name in cfg_copy[cfg_name]:
                if param_name.lower() in HotBackupConfig.SECRET_PARAMETERS:
                    cfg_copy[cfg_name][param_name] = "***"
        return json.dumps(cfg_copy)

    def save_config(self, filename):
        """writes a hotbackup rclone configuration file"""
        fhandle = self.install_prefix / filename
        lh.subsubsection("Writing RClone config:")
        print(self.get_config_json_sanitized())
        fhandle.write_text(self.get_config_json())
        return str(fhandle)

    @step
    def get_rclone_config_file(self):
        """create a config file and return its full name"""
        filename = self.save_config("rclone_config.json")
        attach(self.get_config_json_sanitized(), "rclone_config.json", "application/json", "rclone_config.json")
        return filename

    def construct_remote_storage_path(self, postfix):
        """ generate a working storage path from the config params """
        result = f"{self.name}:/{self.hb_provider_cfg.path_prefix}/{postfix}"
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

    # pylint: disable=too-many-arguments
    @step
    def run_backup(self, arguments, name, silent=False, expect_to_fail=False, timeout=20):
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
            timeout,
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
        self.run_backup(args, backup_name, timeout=120)

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

        out = self.run_backup(args, backup_name, timeout=backup_config.hb_timeout)
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
        out = self.run_backup(args, backup_name, timeout=backup_config.hb_timeout)
        for line in out.split("\n"):
            match = re.match(r".*arangobackup download --status-id=(\d*)", str(line))
            if match:
                return match.group(1)
        raise Exception("couldn't locate name of the upload process!")

    # pylint: disable=unused-argument disable=no-self-use
    def validate_local_backup(self, starter_basedir, backup_name):
        """ validate backups in the local installation """
        self.validate_backup(starter_basedir, backup_name)

    def validate_backup(self, directory, backup_name):
        """ search on the disk whether crash files exist """
        backups_validated = 0
        for meta_file in directory.glob( "**/*META"):
            content = json.loads(meta_file.read_text())
            size = 0
            count = 0
            for one_file in meta_file.parent.glob( "**/*"):
                if one_file.is_dir() or one_file.name == "META":
                    continue
                size += one_file.stat().st_size
                count += 1
            backups_validated += 1
            try:
                if content['countIncludesFilesOnly']:
                    if size != content['sizeInBytes']:
                        raise Exception("Backup has different size than its META indicated! " + str(size) +
                                        " - " + str(content))
                    if count != content['nrFiles']:
                        raise Exception("Backup count of files doesn't match! " + str(count) + " - " + str(content))
                    continue
            except KeyError:
                pass
            print("validation with META not supported. Size: " + str(size) + " META: " + str(content))
        print(str(backups_validated) + " Backups validated: OK")
