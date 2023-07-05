#!/usr/bin/env python3
"""Debug symbols test suite"""
# pylint: disable=import-error
import platform
import re
import shutil
from pathlib import Path

import semver
from allure_commons._allure import attach
from allure_commons.types import AttachmentType

from arangodb.installers import create_config_installer_set
from arangodb.instance import InstanceType
from arangodb.starter.manager import StarterManager
from debugger_tests.debug_test_steps import create_dump_for_exe, create_arangod_dump, store
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import (
    testcase,
    disable_if_returns_true_at_runtime,
    linux_only,
    run_before_suite,
    run_after_suite,
    run_after_each_testcase,
    windows_only,
    collect_crash_data,
    parameters,
    disable,
)
from test_suites_core.cli_test_suite import CliStartedTestSuite, CliTestSuiteParameters
from tools.killall import kill_all_processes

OS_IS_WINDOWS = bool(platform.win32_ver()[0])
if OS_IS_WINDOWS:
    import wexpect


class DebuggerTestSuite(CliStartedTestSuite):
    """Debug symbols test suite"""

    if OS_IS_WINDOWS:
        TMP_DIR = Path("C:\\TMP")
    else:
        TMP_DIR = Path("/tmp")
    TEST_DATA_DIR = TMP_DIR / "DebuggerTestSuite"
    SYMSRV_DIR = TEST_DATA_DIR / "symsrv_rta"
    SYMSRV_CACHE_DIR = TEST_DATA_DIR / "symsrv_cache"
    DUMP_FILES_DIR = TEST_DATA_DIR / "dumps"
    STARTER_DIR = TEST_DATA_DIR / "starter"

    CDB_PROMPT = re.compile(r"^\d{1,3}:\d{1,3}>", re.MULTILINE)

    def __init__(self, params: CliTestSuiteParameters):
        super().__init__(params)
        self.installer_set = create_config_installer_set(
            versions=[self.new_version], 
            base_config=self.base_cfg, 
            deployment_mode="all", 
            run_properties=self.run_props, 
            use_auto_certs=False
        )
        self.installer = self.installer_set[0][1]
        ent = "Enterprise" if self.run_props.enterprise else "Community"
        self.suite_name = (
            f"Debug symbols test suite: ArangoDB v. {str(self.new_version)} ({ent}) ({self.installer.installer_type})"
        )

    def is_zip(self):
        return self.base_cfg.zip_package

    def is_community(self):
        return not self.run_props.enterprise

    @run_before_suite
    def create_test_dirs(self):
        """create test data directories"""
        if DebuggerTestSuite.TEST_DATA_DIR.exists():
            shutil.rmtree(str(DebuggerTestSuite.TEST_DATA_DIR))
        DebuggerTestSuite.TEST_DATA_DIR.mkdir(parents=True)
        DebuggerTestSuite.SYMSRV_DIR.mkdir(parents=True)
        DebuggerTestSuite.SYMSRV_CACHE_DIR.mkdir(parents=True)
        DebuggerTestSuite.DUMP_FILES_DIR.mkdir(parents=True)
        DebuggerTestSuite.STARTER_DIR.mkdir(parents=True)

    @run_before_suite
    def install_packages(self):
        """install server package and debug package"""
        self.installer.uninstall_everything()
        self.installer.cleanup_system()
        self.installer.install_server_package()
        self.installer.stop_service()
        self.installer.install_debug_package()

    @run_after_suite
    def delete_test_dirs(self):
        """delete test data directories"""
        if DebuggerTestSuite.TEST_DATA_DIR.exists():
            shutil.rmtree(str(DebuggerTestSuite.TEST_DATA_DIR))

    @run_after_each_testcase
    def clear_cache_dir(self):
        """clear symsrv cache dir"""
        if DebuggerTestSuite.SYMSRV_CACHE_DIR.exists():
            shutil.rmtree(str(DebuggerTestSuite.SYMSRV_CACHE_DIR))
            DebuggerTestSuite.SYMSRV_CACHE_DIR.mkdir(parents=True)

    @run_after_suite
    def uninstall_everything(self):
        """uninstall all packages"""
        self.installer.un_install_server_package()
        self.installer.un_install_debug_package()
        self.installer.uninstall_everything()
        self.installer.cleanup_system()
        self.installer.cfg.server_package_is_installed = False
        self.installer.cfg.debug_package_is_installed = False
        self.installer.cfg.client_package_is_installed = False

    @run_after_suite
    def teardown_suite(self):
        """Teardown suite environment: Debug symbols test suite"""
        kill_all_processes()
        # If there are failed test cases, save the contents of the installation directories.
        # This must be done not more than once per suite run to save space,
        # therefore it shouldn't be done in a @collect_crash_data method.
        if self.there_are_failed_tests():
            if self.installer.cfg.debug_install_prefix.exists():
                archive = shutil.make_archive(
                    "debug_package_installation_dir",
                    "gztar",
                    self.installer.cfg.debug_install_prefix,
                    self.installer.cfg.debug_install_prefix,
                )
                attach.file(archive, "Debug package installation directory", "application/x-tar", "tgz")
            if self.installer.cfg.install_prefix.exists():
                archive = shutil.make_archive(
                    "server_package_installation_dir",
                    "gztar",
                    self.installer.cfg.install_prefix,
                    self.installer.cfg.install_prefix,
                )
                attach.file(archive, "Server package installation directory", "application/x-tar", "tgz")

    @collect_crash_data
    def save_test_data(self):
        """save test data"""
        test_dir = DebuggerTestSuite.TEST_DATA_DIR
        if test_dir.exists():
            archive = shutil.make_archive("debug_symbols_test_dir", "gztar", test_dir, test_dir)
            attach.file(archive, "Debug symbols test suite directory", "application/x-tar", "tgz")

    disable_for_tar_gz_packages = disable_if_returns_true_at_runtime(
        is_zip, "This test case is not applicable for .tar.gz packages"
    )

    @linux_only
    @disable_for_tar_gz_packages
    @testcase
    def test_debug_symbols_linux(self):
        """Debug arangod executable (Linux)"""
        self.installer.debugger_test()

    def test_debug_symbols_windows(self, executable):
        """Check that debug symbols can be used to debug arango executable using a memory dump file (Windows)"""
        exe_file = [str(file.path) for file in self.installer.arango_binaries if file.path.name == executable + ".exe"][
            0
        ]
        dump_file = create_dump_for_exe(exe_file, DebuggerTestSuite.DUMP_FILES_DIR)
        pdb_dir = str(self.installer.cfg.debug_install_prefix)
        with step("Check that stack trace with function names and line numbers can be acquired from cdb"):
            cmd = " ".join(["cdb", "-z", dump_file, "-y", pdb_dir, "-lines", "-n"])
            attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
            cdb = wexpect.spawn(cmd)
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=180)
            cdb.sendline("k")
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=180)
            stack = cdb.before
            cdb.sendline("q")
            attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
            assert f"{executable}!main" in stack, "Stack must contain real function names."
            assert f"{executable}.cpp" in stack, "Stack must contain real source file names."


    @parameters(
        [
            {"executable": "arangoexport"},
            {"executable": "arangosh"},
            {"executable": "arangoimport"},
            {"executable": "arangodump"},
            {"executable": "arangorestore"},
            {"executable": "arangobench"},
            {"executable": "arangovpack"},
            {"executable": "arangod"},
        ]
    )
    @windows_only
    @testcase("Debug {executable} executable using a memory dump file (Windows)")
    def test_debug_symbols_windows_community(self, executable):
        self.test_debug_symbols_windows(executable)

    @parameters([{"executable": "arangobackup"}])
    @disable_if_returns_true_at_runtime(is_community, "This testcase is not applicable to community packages.")
    @windows_only
    @testcase("Debug {executable} executable using a memory dump file (Windows)")
    def test_debug_symbols_windows_enterprise(self, executable):
        self.test_debug_symbols_windows(executable)

    @windows_only
    @testcase
    def test_debug_symbols_attach_to_process_windows(self):
        """Debug arangod executable by attaching debugger to a running process (Windows)"""
        starter = StarterManager(
            basecfg=self.installer.cfg,
            install_prefix=Path(DebuggerTestSuite.STARTER_DIR),
            instance_prefix="single",
            expect_instances=[InstanceType.SINGLE],
            mode="single",
            jwt_str="single",
            moreopts=[],
        )
        try:
            with step("Start a single server deployment"):
                starter.run_starter()
                starter.detect_instances()
                starter.detect_instance_pids()
                starter.set_passvoid("")
                pid = starter.all_instances[0].pid
            pdb_dir = str(self.installer.cfg.debug_install_prefix)
            with step("Check that stack trace with function names and line numbers can be acquired from cdb"):
                cmd = " ".join(["cdb", "-pv", "-p", str(pid), "-y", pdb_dir, "-lines", "-n"])
                attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
                cdb = wexpect.spawn(cmd)
                cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=300)
                cdb.sendline("k")
                cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=300)
                stack = cdb.before
                cdb.sendline("q")
                attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
                assert "arangod!main" in stack, "Stack must contain real function names."
                assert "arangod.cpp" in stack, "Stack must contain real source file names."
        finally:
            starter.terminate_instance()
            kill_all_processes()

    @windows_only
    @testcase
    def test_debug_symbols_symsrv_windows(self):
        """Debug arangod executable using symbol server (Windows)"""
        symsrv_dir = str(DebuggerTestSuite.SYMSRV_DIR)
        store(str(self.installer.cfg.debug_install_prefix / "arangod.pdb"), symsrv_dir)
        exe_file = [str(file.path) for file in self.installer.arango_binaries if file.path.name == "arangod.exe"][0]
        dump_file = create_dump_for_exe(exe_file, DebuggerTestSuite.DUMP_FILES_DIR)
        with step("Check that stack trace with function names and line numbers can be acquired from cdb"):
            cmd = " ".join(
                [
                    "cdb",
                    "-z",
                    dump_file,
                    "-y",
                    f"srv*{DebuggerTestSuite.SYMSRV_CACHE_DIR}*{DebuggerTestSuite.SYMSRV_DIR}",
                    "-lines",
                    "-n",
                ]
            )
            attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
            cdb = wexpect.spawn(cmd)
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=900)
            cdb.sendline("k")
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=900)
            stack = cdb.before
            cdb.sendline("q")
            attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
            assert "arangod!main" in stack, "Stack must contain real function names."
            assert "arangod.cpp" in stack, "Stack must contain real source file names."

    @windows_only
    @disable("This test case must only be ran manually")
    @testcase
    def test_debug_network_symbol_server_windows(self):
        """Check that debug symbols can be found on the ArangoDB symbol server and then used to debug arangod executable"""
        # This testcase is needed to check the state of the symbol server and is not meant
        # to run during ArangoDB product testing.
        version = semver.VersionInfo.parse(self.installer.cfg.version)
        symsrv_dir = "\\\\symbol.arangodb.biz\\symbol\\symsrv_arangodb" + str(version.major) + str(version.minor)
        dump_file = create_arangod_dump(
            self.installer, str(DebuggerTestSuite.STARTER_DIR), str(DebuggerTestSuite.DUMP_FILES_DIR)
        )
        with step("Check that stack trace with function names and line numbers can be acquired from cdb"):
            cmd = " ".join(
                [
                    "cdb",
                    "-z",
                    dump_file,
                    "-y",
                    f"srv*{DebuggerTestSuite.SYMSRV_CACHE_DIR}*{symsrv_dir}",
                    "-lines",
                    "-n",
                ]
            )
            attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
            cdb = wexpect.spawn(cmd)
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=900)
            cdb.sendline("k")
            cdb.expect(DebuggerTestSuite.CDB_PROMPT, timeout=900)
            stack = cdb.before
            cdb.sendline("q")
            attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
            assert "arangod!main" in stack, "Stack must contain real function names."
            assert "arangod.cpp" in stack, "Stack must contain real source file names."
