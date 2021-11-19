#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
import logging
import sys
from pathlib import Path

import tools.errorhelper as eh
from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    dummy_line_result,
)
from reporting.reporting_utils import step

ON_POSIX = "posix" in sys.builtin_module_names


class ArangoshExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    def __init__(self, config, connect_instance):
        self.read_only = False
        super().__init__(config, connect_instance)

    def run_command(self, cmd, verbose=True, timeout=300, result_line=dummy_line_result, expect_to_fail=False):
        """run a command in arangosh"""
        title = f"run a command in arangosh: {cmd[0]}"
        with step(title):
            executable = self.cfg.bin_dir / "arangosh"
            arangosh_args = ["--log.level", "v8=debug", "--javascript.execute-string"]
            arangosh_args += cmd[1:]
            return self.run_arango_tool_monitored(
                executeable=executable,
                more_args=arangosh_args,
                timeout=timeout,
                result_line=result_line,
                verbose=verbose,
                expect_to_fail=expect_to_fail,
            )

    @step
    def self_test(self):
        """run a command that throws to check exit code handling"""
        logging.info("running arangosh check")
        success = self.run_command(
            ("check throw exit codes", "throw 'yipiahea motherfucker'"),
            self.cfg.verbose,
        )
        logging.debug("sanity result: " + str(success) + " - expected: False")

        if success:
            raise Exception("arangosh doesn't exit with non-0 to indicate errors")

        success = self.run_command(("check normal exit", 'let foo = "bar"'), self.cfg.verbose)

        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception("arangosh doesn't exit with 0 to indicate no errors")

    @step
    def run_script_monitored(
        self,
        cmd,
        args,
        timeout,
        result_line,
        process_control=False,
        verbose=True,
        expect_to_fail=False,
    ):
        # pylint: disable=R0913 disable=R0902 disable=R0915 disable=R0912 disable=R0914
        """
        runs a script in background tracing with
        a dynamic timeout that its got output
        (is still alive...)
        """
        if process_control:
            process_control = ["--javascript.allow-external-process-control", "true"]
        else:
            process_control = []
        # fmt: off
        run_cmd = [
            "--log.level", "v8=debug",
            "--javascript.module-directory", self.cfg.test_data_dir.resolve(),
        ] + process_control + [
            "--javascript.execute", str(cmd[1])
        ]
        # fmt: on

        if len(args) > 0:
            run_cmd += ["--"] + args

        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangosh",
            run_cmd,
            timeout,
            result_line,
            verbose,
            expect_to_fail,
        )

    @step
    def js_version_check(self):
        """run a version check command; this can double as password check"""
        logging.info("running version check")
        semdict = dict(self.cfg.semver.to_dict())
        version = "{major}.{minor}.{patch}".format(**semdict)
        js_script_string = """
            const version = db._version().substring(0, {1});
            if (version != "{0}") {{
                throw `version check failed: ${{version}} (current) !- {0} (requested)`
            }}
        """.format(
            version, len(version)
        )

        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(["check version", js_script_string], self.cfg.verbose)
        logging.debug("version check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("version check failed", self.cfg.interactive)
        return res

    @step
    def js_set_passvoid(self, user, passvoid):
        """connect to the instance, and set a passvoid for the user"""
        js_set_passvoid_str = 'require("org/arangodb/users").update("%s", "%s");' % (
            user,
            passvoid,
        )
        logging.debug("script to be executed: " + str(js_set_passvoid_str))
        res = self.run_command(["set passvoid", js_set_passvoid_str], self.cfg.verbose)
        logging.debug("set passvoid check result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("setting passvoid failed", self.cfg.interactive)
        return res

    @step(
        """Create a collection with documents after taking a backup
          (to verify its not in the backup)"""
    )
    def hotbackup_create_nonbackup_data(self):
        """
        create a collection with documents after taking a backup
        to verify its not in the backup
        """
        logging.info("creating volatile testdata")
        js_script_string = """
            db._create("this_collection_will_not_be_backed_up");
            db.this_collection_will_not_be_backed_up.save(
               {"this": "document will be gone"});
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(["create volatile data", js_script_string], True)  # self.cfg.verbose)
        logging.debug("data create result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("creating volatile testdata failed", self.cfg.interactive)
        return res

    @step
    def hotbackup_check_for_nonbackup_data(self):
        """check whether the data is in there or not."""
        logging.info("running version check")
        #  || db.this_collection_will_not_be_backed_up._length() != 0
        # // do we care?
        js_script_string = """
            if (db._collection("this_collection_will_not_be_backed_up")
                 != null) {
              throw `data is there!`;
            }
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(["check whether non backup data exists", js_script_string], True)  # self.cfg.verbose)
        logging.debug("data check result: " + str(res))

        return res

    @step
    def run_in_arangosh(self, testname, args=[], moreargs=[], result_line=dummy_line_result, timeout=100):
        # pylint: disable=R0913 disable=R0902 disable=W0102
        """mimic runInArangosh testing.js behaviour"""
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        ret = None

        try:
            cwd = Path.cwd()
            (cwd / "3rdParty").mkdir()
            (cwd / "arangosh").mkdir()
            (cwd / "arangod").mkdir()
            (cwd / "tests").mkdir()
        except FileExistsError:
            pass
        ret = self.run_script_monitored(
            cmd=[
                "setting up test data",
                self.cfg.test_data_dir.resolve() / "run_in_arangosh.js",
            ],
            args=[testname] + args + ["--args"] + moreargs,
            timeout=timeout,
            result_line=result_line,
            process_control=True,
            verbose=self.cfg.verbose,
        )
        return ret

    @step
    def create_test_data(self, testname, args=[], result_line=dummy_line_result, timeout=100):
        # pylint: disable=W0102
        """deploy testdata into the instance"""
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")

        ret = self.run_script_monitored(
            cmd=[
                "setting up test data",
                self.cfg.test_data_dir.resolve() / "makedata.js",
            ],
            args=args + ["--progress", "true", "--passvoid", self.cfg.passvoid],
            timeout=timeout,
            result_line=result_line,
            verbose=self.cfg.verbose,
        )

        return ret

    @step
    def check_test_data(self, testname, supports_foxx_tests, args=[], result_line=dummy_line_result):
        # pylint: disable=W0102
        """check back the testdata in the instance"""
        if testname:
            logging.info("checking test data for {0}".format(testname))
        else:
            logging.info("checking test data")

        ret = self.run_script_monitored(
            cmd=["checking test data integrity", self.cfg.test_data_dir.resolve() / "checkdata.js"],
            # fmt: off
            args=args + [
                '--progress', 'true',
                '--oldVersion', self.cfg.version,
                '--testFoxx', 'true' if supports_foxx_tests else 'false'
            ],
            # fmt: on
            timeout=25,
            result_line=result_line,
            verbose=self.cfg.verbose,
        )
        return ret

    @step
    def clear_test_data(self, testname, args=[], result_line=dummy_line_result):
        # pylint: disable=W0102
        """flush the testdata from the instance again"""
        if testname:
            logging.info("removing test data for {0}".format(testname))
        else:
            logging.info("removing test data")

        ret = self.run_script_monitored(
            cmd=[
                "cleaning up test data",
                self.cfg.test_data_dir.resolve() / "cleardata.js",
            ],
            args=args + ["--progress", "true"],
            timeout=5,
            result_line=result_line,
            verbose=self.cfg.verbose,
        )

        return ret
