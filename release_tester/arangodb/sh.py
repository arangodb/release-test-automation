#!/usr/bin/env python
""" Run a javascript command by spawning an arangosh
    to the configured connection """
from datetime import datetime
import logging
import sys
from pathlib import Path

import tools.errorhelper as eh
from arangodb.async_client import (
    ArangoCLIprogressiveTimeoutExecutor,
    default_line_result,
    make_default_params,
    CliExecutionException)
from reporting.reporting_utils import step

ON_POSIX = "posix" in sys.builtin_module_names


class ArangoshExecutor(ArangoCLIprogressiveTimeoutExecutor):
    """configuration"""

    def __init__(self, config, connect_instance, old_version):
        self.read_only = False
        super().__init__(config, connect_instance)
        self.old_version = old_version

    # pylint: disable=too-many-arguments
    def run_command(
        self,
        cmd,
        verbose=True,
        use_default_auth=True,
        progressive_timeout=300,
        deadline=300,
        expect_to_fail=False,
        result_line_handler=default_line_result,
    ):
        """run a command in arangosh"""
        title = f"run a command in arangosh: {cmd[0]}"
        with step(title):
            executable = self.cfg.bin_dir / "arangosh"
            arangosh_args = self.cfg.default_arangosh_args + [
                "--log.level",
                "v8=debug",
                "--log.level",
                "httpclient=debug",
                "--javascript.execute-string",
            ]
            arangosh_args += cmd[1:]
            return self.run_arango_tool_monitored(
                executeable=executable,
                more_args=arangosh_args,
                use_default_auth=use_default_auth,
                params=make_default_params(verbose, cmd[0]),
                progressive_timeout=progressive_timeout,
                deadline=deadline,
                result_line_handler=result_line_handler,
                expect_to_fail=expect_to_fail,
            )

    @step
    def self_test(self):
        """run a command that throws to check exit code handling"""
        logging.info("running arangosh check")
        result = self.run_command(
            ("check throw exit codes", "throw 'thy shall not pass!'"),
            verbose=self.cfg.verbose,
            expect_to_fail=True,
        )
        success = result[0]
        logging.debug("sanity result: " + str(success) + " - expected: False")

        if success:
            raise Exception("arangosh doesn't exit with non-0 to indicate errors")

        success = self.run_command(("check normal exit", 'let foo = "bar"'), self.cfg.verbose)

        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception("arangosh doesn't exit with 0 to indicate no errors")
        result = self.run_script_monitored(
            cmd=["checking throw to exit 1", self.cfg.test_data_dir.resolve() / "check_throw_exitcode.js"],
            args=[],
            progressive_timeout=25,
            result_line_handler=default_line_result,
            verbose=self.cfg.verbose,
            expect_to_fail=True,
        )
        success = result[0]
        logging.debug("sanity result: " + str(success) + " - expected: False")

        if success:
            raise Exception("arangosh doesn't exit with non-0 to indicate errors")

        result = self.run_script_monitored(
            cmd=["checking test data integrity", self.cfg.test_data_dir.resolve() / "check_exit.js"],
            args=[],
            progressive_timeout=25,
            result_line_handler=default_line_result,
            verbose=self.cfg.verbose,
        )
        success = result[0]
        logging.debug("sanity result: " + str(success) + " - expected: True")

        if not success:
            raise Exception("arangosh doesn't exit with 0 to indicate no errors")

    @step
    def run_script_monitored(
        self,
        cmd,
        args,
        progressive_timeout,
        deadline=1000,
        result_line_handler=default_line_result,
        process_control=False,
        verbose=True,
        expect_to_fail=False,
        log_debug=False,
    ):
        # pylint: disable=too-many-arguments disable=too-many-instance-attributes disable=too-many-statements disable=too-many-branches disable=too-many-locals
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
        run_cmd = self.cfg.default_arangosh_args + [
            "--log.level", "v8=debug",
            "--javascript.module-directory", self.cfg.test_data_dir.resolve(),
        ] + process_control + [
            "--javascript.execute", str(cmd[1])
        ]
        if log_debug:
            run_cmd += [
                "--log.level", "startup=trace", # BTS-1743 - find out why arangosh exits
            ]
        # fmt: on

        if len(args) > 0:
            run_cmd += ["--"] + args

        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangosh",
            run_cmd,
            use_default_auth=True,
            params=make_default_params(verbose, cmd[0]),
            progressive_timeout=progressive_timeout,
            result_line_handler=result_line_handler,
            expect_to_fail=expect_to_fail,
            deadline=deadline,
        )

    def run_testing(
        self,
        testcase,
        testing_args,
        progressive_timeout,
        directory,
        # logfile,
        verbose,
    ):
        # pylint: disable=R0913 disable=R0902
        """testing.js wrapper"""
        args = [
            self.cfg.bin_dir / "arangosh",
            "-c",
            str(self.cfg.cfgdir / "arangosh.conf"),
            "--log.level",
            "warning",
            "--log.level",
            "v8=debug",
            "--server.endpoint",
            "none",
            "--javascript.allow-external-process-control",
            "true",
            "--javascript.execute",
            str(Path("UnitTests") / "unittest.js"),
        ]
        run_cmd = args + ["--", testcase, "--testOutput", directory] + testing_args
        return self.run_arango_tool_monitored(
            self.cfg.bin_dir / "arangosh",
            run_cmd,
            progressive_timeout,
            default_line_result,
            verbose,
            False,
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
        js_set_passvoid_str = f"""
        if (!arango.isConnected()) {{
          throw new Error('connecting the database failed');
        }}
        require('org/arangodb/users').update('{user}', '{passvoid}');
        """
        logging.debug("script to be executed: " + str(js_set_passvoid_str))
        res = self.run_command(["set passvoid", js_set_passvoid_str], self.cfg.verbose)
        logging.debug("set passvoid check result: " + str(res))
        self.cfg.passvoid = passvoid

        if not res:
            eh.ask_continue_or_exit("setting passvoid failed", self.cfg.interactive)
        return res

    @step
    def hotbackup_create_nonbackup_data(self, suff=""):
        """
        create a collection with documents after taking a backup
        to verify its not in the backup
        """
        logging.info("creating volatile testdata")
        js_script_string = f"""
            if (!arango.isConnected()) {{
              throw new Error('connecting the database failed');
            }}
            db._create("this_collection_will_not_be_backed_up{suff}");
            db.this_collection_will_not_be_backed_up{suff}.save(
               {{"this": "document will be gone"}});
        """
        logging.debug("script to be executed: " + str(js_script_string) + str(self.connect_instance))
        res = self.run_command(["create volatile data", js_script_string], True)  # self.cfg.verbose)
        logging.debug("data create result: " + str(res))

        if not res:
            eh.ask_continue_or_exit("creating volatile testdata failed", self.cfg.interactive)
        return res

    @step
    def hotbackup_check_for_nonbackup_data(self, suff=""):
        """check whether the data is in there or not."""
        logging.info("running check of volatile data")
        #  || db.this_collection_will_not_be_backed_up._length() != 0
        # // do we care?
        js_script_string = f"""
            if (!arango.isConnected()) {{
              throw new Error('connecting the database failed');
            }}
            if (db._collection("this_collection_will_not_be_backed_up{suff}")
                 != null) {{
              throw new Error(`data is there!`);
            }}
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(["check whether non backup data exists", js_script_string], True)  # self.cfg.verbose)
        logging.debug("data check result: " + str(res))

        return res

    @step
    def hotbackup_wait_for_ready_after_restore(self):
        """check that array with databases is not empty."""
        logging.info("running database readiness check")
        js_script_string = """
        if (!arango.isConnected()) {
          throw new Error('connecting the database failed');
        }
        let timeout = 60;
        while (db._databases().length == 0)  {
          if (timeout == 0) {
            throw new Error("Databases array is still empty after 15s!");
          }
          require("internal").sleep(1);
          timeout -= 1;
          print('.');
        }
        """
        logging.debug("script to be executed: " + str(js_script_string))
        res = self.run_command(["check whether all databases were restored", js_script_string], self.cfg.verbose)
        logging.debug("SUT readiness result: " + str(res))

        return res

    @step
    def run_in_arangosh(
        self,
        testname,
        args=None,
        moreargs=None,
        result_line_handler=default_line_result,
        deadline=1000,
        progressive_timeout=100,
        log_debug=False,
    ):
        """mimic runInArangosh testing.js behaviour"""
        # pylint: disable=too-many-arguments disable=too-many-instance-attributes
        if args is None:
            args = []
        if moreargs is None:
            moreargs = []
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
        try:
            ret = self.run_script_monitored(
                cmd=[
                    "setting up test data",
                    self.cfg.test_data_dir.resolve() / "run_in_arangosh.js",
                ],
                args=[testname] + args + ["--args"] + moreargs,
                progressive_timeout=progressive_timeout,
                result_line_handler=result_line_handler,
                process_control=True,
                verbose=self.cfg.verbose,
                deadline=deadline,
                log_debug=log_debug,
            )
        except CliExecutionException as ex:
            print(f"{datetime.now()}execution of {testname} failed. Its output was: \n{ex.message}")
            raise ex
        return ret

    @step
    def create_test_data(
        self,
        testname,
        args=None,
        result_line_handler=default_line_result,
        progressive_timeout=100,
        deadline=900,
        one_shard: bool = False,
        database_name: str = "_system",
    ):
        """deploy testdata into the instance"""
        if args is None:
            args = []
        args = [database_name] + args
        if one_shard:
            args += ["--singleShard", "true", "--createOneShardDatabase", "true"]
        if testname:
            logging.info("adding test data for {0}".format(testname))
        else:
            logging.info("adding test data")
        test_filter = []
        if self.cfg.test != "":
            test_filter = ["--test", self.cfg.test]
        ret = self.run_script_monitored(
            cmd=[
                "setting up test data",
                self.cfg.test_data_dir.resolve() / "makedata.js",
            ],
            args=args + ["--progress", "true", "--passvoid", self.cfg.passvoid] + test_filter,
            progressive_timeout=progressive_timeout,
            result_line_handler=result_line_handler,
            deadline=deadline,
        )

        return ret

    @step
    def check_test_data(
        self,
        testname,
        supports_foxx_tests,
        args=None,
        one_shard: bool = False,
        database_name: str = "_system",
        result_line_handler=default_line_result,
        log_debug=False,
        deadline=900,
        progressive_timeout=25
    ):
        """check back the testdata in the instance"""
        if args is None:
            args = []
        args = [database_name] + args
        if one_shard:
            args += ["--singleShard", "true"]
        if testname:
            logging.info("checking test data for {0}".format(testname))
        else:
            logging.info("checking test data")

        test_filter = []
        if self.cfg.test != "":
            test_filter = ["--test", self.cfg.test]
        ret = self.run_script_monitored(
            cmd=["checking test data integrity", self.cfg.test_data_dir.resolve() / "checkdata.js"],
            # fmt: off
            args=args + [
                '--progress', 'true',
                '--oldVersion', self.old_version,
                '--testFoxx', 'true' if supports_foxx_tests else 'false',
                '--passvoid', self.cfg.passvoid
            ] + test_filter,
            # fmt: on
            progressive_timeout=progressive_timeout,
            result_line_handler=result_line_handler,
            verbose=self.cfg.verbose or log_debug,
            log_debug=log_debug,
            deadline=deadline,
        )
        return ret

    @step
    def clear_test_data(self, testname, args=None, result_line_handler=default_line_result):
        """flush the testdata from the instance again"""
        if args is None:
            args = []
        if testname:
            logging.info("removing test data for {0}".format(testname))
        else:
            logging.info("removing test data")

        test_filter = []
        if self.cfg.test != "":
            test_filter = ["--test", self.cfg.test]
        ret = self.run_script_monitored(
            cmd=[
                "cleaning up test data",
                self.cfg.test_data_dir.resolve() / "cleardata.js",
            ]
            + test_filter,
            args=args + ["--progress", "true"],
            progressive_timeout=5,
            result_line_handler=result_line_handler,
        )

        return ret
