#!/usr/bin/env python3
"""Debug symbols test suite"""
import platform
import shutil
from pathlib import Path

import semver
from allure_commons._allure import attach
from allure_commons.types import AttachmentType

from arangodb.installers import InstallerBaseConfig, create_config_installer_set
from debugger_tests.debug_test_steps import create_arangod_dump, store
from reporting.reporting_utils import step
from test_suites_core.base_test_suite import (
    testcase,
    disable_if_returns_true_at_runtime,
    linux_only,
    BaseTestSuite,
    run_before_suite,
    run_after_suite,
    run_after_each_testcase,
    windows_only, collect_crash_data, disable,
)
from tools.killall import kill_all_processes

os_is_windows = bool(platform.win32_ver()[0])
if os_is_windows:
    import wexpect


class DebuggerTestSuite(BaseTestSuite):
    """Debug symbols test suite"""

    if os_is_windows:
        TMP_DIR = Path("C:\\TMP")
    else:
        TMP_DIR = Path("/tmp")
    TEST_DATA_DIR = TMP_DIR / "DebuggerTestSuite"
    SYMSRV_DIR = TEST_DATA_DIR / "symsrv_rta"
    SYMSRV_CACHE_DIR = TEST_DATA_DIR / "symsrv_cache"
    DUMP_FILES_DIR = TEST_DATA_DIR / "dumps"
    STARTER_DIR = TEST_DATA_DIR / "starter"

    def __init__(self, versions: list, base_config: InstallerBaseConfig, **kwargs):
        run_props = kwargs["run_props"]
        if len(versions) > 1:
            self.new_version = versions[1]
        else:
            self.new_version = versions[0]
        self.base_cfg = base_config
        self.auto_generate_parent_test_suite_name = False
        self.use_subsuite = False
        self.installer_set = create_config_installer_set(
            versions=[self.new_version], base_config=self.base_cfg, deployment_mode="all", run_properties=run_props
        )
        self.installer = self.installer_set[0][1]
        ent = "Enterprise" if run_props.enterprise else "Community"
        self.suite_name = (
            f"Debug symbols test suite: ArangoDB v. {str(self.new_version)} ({ent}) ({self.installer.installer_type})"
        )
        super().__init__()

    def is_zip(self):
        return self.base_cfg.zip_package

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

    @run_before_suite
    @run_after_suite
    @run_after_each_testcase
    def uninstall_everything(self):
        """uninstall all packages"""
        self.installer.uninstall_everything()
        self.installer.cleanup_system()
        self.installer.cfg.server_package_is_installed = False
        self.installer.cfg.debug_package_is_installed = False
        self.installer.cfg.client_package_is_installed = False

    @run_after_suite
    def teardown_suite(self):
        """Teardown suite environment: Debug symbols test suite"""
        kill_all_processes()

    @collect_crash_data
    def save_test_data(self):
        """save test data"""
        test_dir = DebuggerTestSuite.TEST_DATA_DIR
        if test_dir.exists():
            archive = shutil.make_archive("debug_symbols_test_dir", "bztar", test_dir, test_dir)
            attach.file(archive, "Debug symbols test suite directory", "application/x-bzip2", "tar.bz2")

    disable_for_tar_gz_packages = disable_if_returns_true_at_runtime(
        is_zip, "This test case is not applicable for .tar.gz packages"
    )

    @linux_only
    @disable_for_tar_gz_packages
    @testcase
    def test_debug_symbols_linux(self):
        """Check that debug symbols can be used to debug arangod executable (Linux)"""
        self.installer.install_server_package()
        self.installer.install_debug_package()
        self.installer.debugger_test()

    @windows_only
    @testcase
    def test_debug_symbols_windows(self):
        """Check that debug symbols can be used to debug arangod executable (Windows)"""
        self.installer.install_server_package()
        self.installer.stop_service()
        self.installer.install_debug_package()
        dump_file = create_arangod_dump(self.installer, DebuggerTestSuite.STARTER_DIR, DebuggerTestSuite.DUMP_FILES_DIR)
        pdb_dir = str(self.installer.cfg.debug_install_prefix)
        with step("Check that stack trace with function names and line numbers can be acquired from cdb"):
            cmd = " ".join(["cdb", "-z", dump_file, "-y", pdb_dir, "-lines", "-n"])
            attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
            cdb = wexpect.spawn(cmd)
            cdb.expect("0:000>")
            cdb.sendline("k")
            cdb.expect("0:000>")
            stack = cdb.before
            cdb.sendline("q")
            attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
            assert "arangod!main" in stack, "Stack must contain real function names."
            assert "arangod.cpp" in stack, "Stack must contain real source file names."

    @windows_only
    @testcase
    def test_debug_symbols_symsrv_windows(self):
        """Check that debug symbols can be uploaded to symbol server and then used to debug arangod executable (Windows)"""
        self.installer.install_server_package()
        self.installer.stop_service()
        self.installer.install_debug_package()
        symsrv_dir = str(DebuggerTestSuite.SYMSRV_DIR)
        store(str(self.installer.cfg.debug_install_prefix / "arangod.pdb"), symsrv_dir)
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
                    f"srv*{DebuggerTestSuite.SYMSRV_CACHE_DIR}*{DebuggerTestSuite.SYMSRV_DIR}",
                    "-lines",
                    "-n",
                ]
            )
            attach(cmd, "CDB command", attachment_type=AttachmentType.TEXT)
            cdb = wexpect.spawn(cmd)
            cdb.expect("0:000>")
            cdb.sendline("k")
            cdb.expect("0:000>")
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
        #This testcase is needed to check the state of the symbol server and is not meant to run during ArangoDB product testing.
        self.installer.install_server_package()
        self.installer.stop_service()
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
            cdb.expect("0:000>")
            cdb.sendline("k")
            cdb.expect("0:000>")
            stack = cdb.before
            cdb.sendline("q")
            attach(stack, "Stacktrace from cdb output", attachment_type=AttachmentType.TEXT)
            assert "arangod!main" in stack, "Stack must contain real function names."
            assert "arangod.cpp" in stack, "Stack must contain real source file names."