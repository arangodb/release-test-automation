#!/usr/bin/env python
""" Manage one instance of the arangodb starter
    to crontroll multiple arangods
"""
import copy
import logging
from reporting.reporting_utils import step
import semver
from tools.versionhelper import is_higher_version

from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    make_default_params,
    convert_result,
    expect_failure,
    CliExecutionException,
)


class SyncManager(ArangoCLIprogressiveTimeoutExecutor):
    """manage arangosync"""

    def __init__(self, basecfg, certificate_auth, clusterports, version):
        self.cfg = copy.deepcopy(basecfg)
        self.certificate_auth = certificate_auth
        self.clusterports = clusterports
        self.arguments = [
            "configure",
            "sync",
            "--master.endpoint=https://{ip}:{port}".format(ip=self.cfg.publicip, port=str(clusterports[0])),
            "--master.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
            "--source.endpoint=https://{ip}:{port}".format(ip=self.cfg.publicip, port=str(clusterports[1])),
            "--master.cacert=" + str(self.certificate_auth["cert"]),
            "--source.cacert=" + str(self.certificate_auth["cert"]),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
        ]
        self.version = version
        self.instance = None
        super().__init__(basecfg, None)

    @step
    def run_syncer(self):
        """launch the syncer for this instance"""
        params = make_default_params(self.cfg.verbose)
        ret = self.run_monitored(self.cfg.bin_dir / "arangosync", self.arguments, params=params, deadline=999)
        return expect_failure(False, ret, params)

    def replace_binary_for_upgrade(self, new_install_cfg):
        """set the new config properties"""
        self.cfg.install_prefix = new_install_cfg.install_prefix

    @step
    def check_sync_status(self, which):
        """run the syncer status command"""
        logging.info("SyncManager: Check status of cluster %s", str(which))
        args = [
            "get",
            "status",
            "--master.cacert=" + str(self.certificate_auth["cert"]),
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[which])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
            "--verbose",
        ]
        params = make_default_params(self.cfg.verbose)
        ret = self.run_monitored(
            self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=60, deadline=360
        )

        # "Database.*Collection.*Shard.*Duration"
        return expect_failure(False, ret, params)

    @step
    def get_sync_tasks(self, which):
        """run the get tasks command"""
        logging.info("SyncManager: Check tasks of cluster %s", str(which))
        args = [
            "get",
            "tasks",
            "--master.cacert=" + str(self.certificate_auth["cert"]),
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[which])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
            "--verbose",
        ]
        params = make_default_params(self.cfg.verbose)
        ret = self.run_monitored(
            self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=60, deadline=240
        )
        return expect_failure(False, ret, params)

    @step
    # pylint: disable=dangerous-default-value
    def stop_sync(self, timeout=60, deadline=180, more_args=[]):
        """run the stop sync command"""
        args = [
            "stop",
            "sync",
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[0])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
        ] + more_args
        if is_higher_version(self.version, semver.VersionInfo.parse("2.18.0")):
            args = args + [f"--timeout={round(timeout*0.95)}s"]
        logging.info("SyncManager: stopping sync: %s", str(args))
        params = make_default_params(self.cfg.verbose)
        ret = self.run_monitored(
            self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=timeout, deadline=deadline
        )
        if ret["rc_exit"] != 0:
            print("trying to stop a second time:")
            ret = self.run_monitored(
                self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=timeout, deadline=deadline
            )
        return expect_failure(False, ret, params)

    @step
    def abort_sync(self):
        """run the stop sync command"""
        args = [
            "abort",
            "sync",
            "--timeout=5m",
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[0])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
        ]
        logging.info("SyncManager: stopping sync: %s", str(args))
        params = make_default_params(self.cfg.verbose)
        ret = self.run_monitored(
            self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=60, deadline=300
        )
        return expect_failure(False, ret, params)

    @step
    def check_sync(self):
        """run the check sync command"""
        if self.version < semver.VersionInfo.parse("1.0.0"):
            logging.warning("SyncManager: checking sync consistency: available since 1.0.0 of arangosync")
            return ("", "", True)

        args = [
            "check",
            "sync",
            "--master.cacert=" + str(self.certificate_auth["cert"]),
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[0])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
        ]
        bin_path = self.cfg.bin_dir / "arangosync"
        logging.info("SyncManager: checking sync consistency: %s %s.", bin_path, str(args))
        params = make_default_params(self.cfg.verbose)
        try:
            params = make_default_params(self.cfg.verbose)
            ret = self.run_monitored(
                executeable=bin_path,
                args=args,
                params=params,
                progressive_timeout=60,
                deadline=300,
            )
            return expect_failure(False, ret, params)
        except CliExecutionException as exc:
            result = exc.execution_result
            return result
        print("checking for magic ok string")
        output = convert_result(params["output"])
        success = output.find("The whole data is the same") >= 0
        print("done")
        return (success, output)

    @step
    def reset_failed_shard(self, database, collection):
        """run the reset failed shard command"""
        if self.version < semver.VersionInfo.parse("1.0.0"):
            logging.warning("SyncManager: checking sync consistency: available since 1.0.0 of arangosync")
            return True

        args = [
            "reset",
            "failed",
            "shard",
            "--master.cacert=" + str(self.certificate_auth["cert"]),
            "--master.endpoint=https://{url}:{port}".format(url=self.cfg.publicip, port=str(self.clusterports[0])),
            "--auth.keyfile=" + str(self.certificate_auth["clientkeyfile"]),
            "--database",
            database,
            "--collection",
            collection,
        ]
        logging.info("SyncManager: resetting failed shard: %s", str(args))
        try:
            params = make_default_params(self.cfg.verbose)
            ret = self.run_monitored(
                self.cfg.bin_dir / "arangosync", args, params=params, progressive_timeout=60, deadline=300
            )
            expect_failure(False, ret, params)
            return True
        except CliExecutionException:
            return False
