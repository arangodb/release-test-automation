#!/usr/bin/env python3
""" class to inspect the binaries installed with the packages """
from pathlib import Path
import platform
import re
import logging
import shutil
import subprocess
import time

import magic
import semver
import psutil

from allure_commons._allure import attach
from reporting.reporting_utils import step
# pylint: disable=broad-exception-raised disable=broad-exception-caught
FILE_PIDS = []

IS_WINDOWS = platform.win32_ver()[0]
FILE_EXTENSION = ""
if IS_WINDOWS:
    FILE_EXTENSION = ".exe"


IS_MAC = False
if platform.mac_ver()[0]:
    IS_MAC = True


PROP_NAMES = {
    'Comments': '@binary_version',
    'InternalName': '@binary',
    'ProductName': '@binary',
    'CompanyName': '@company_name',
    'LegalCopyright': r'[ArangoDB GmbH ]*\(C\) Copyright 20.*',
    'ProductVersion': '@windows_version',
    'FileDescription': '@friendly_name',
    'LegalTrademarks': None,
    'PrivateBuild': None,
    'FileVersion': '@windows_version',
    'OriginalFilename': '@binary',
    'SpecialBuild': None
}
## helper classes
class BinaryDescription:
    # pylint: disable=too-many-instance-attributes
    """describe the availability of an arangodb binary and its properties"""

    def __init__(self, path, name, friendly, enter, strip, vmin, vmax, sym, binary_type):
        # pylint: disable=too-many-arguments
        self.path = path / (name + FILE_EXTENSION)
        self.enterprise = enter
        self.stripped = strip
        self.version_min =  semver.VersionInfo.parse(vmin)
        self.version_max =  semver.VersionInfo.parse(vmax)
        self.symlink = sym
        self.binary_type = binary_type
        self.name = name
        self.friendly_name = friendly

        for attribute in (
            self.path,
            self.enterprise,
            self.stripped,
            self.version_min,
            self.version_max,
            self.symlink,
            self.binary_type,
        ):
            if attribute is None:
                logging.error("one of the given args is null")
                logging.error(str(self))
                raise ValueError

    def __repr__(self):
        return """
        path:        {0.path}
        friendly name: {0.friendly_name}
        enterprise:  {0.enterprise}
        stripped:    {0.stripped}
        version_min: {0.version_min}
        version_max: {0.version_max}
        symlink:     {0.symlink}
        binary_type: {0.binary_type}
        """.format(
            self
        )

    def _validate_notarization(self, enterprise):
        """check whether this binary is notarized"""
        if not enterprise and self.enterprise:
            return
        if IS_MAC:
            cmd = ["codesign", "--verify", "--verbose", str(self.path)]
            check_strings = [b"valid on disk", b"satisfies its Designated Requirement"]
            with psutil.Popen(cmd, bufsize=-1, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
                (_, codesign_str) = proc.communicate()
                if proc.returncode:
                    raise Exception("codesign exited nonzero " + str(cmd) + "\n" + str(codesign_str))
                if codesign_str.find(check_strings[0]) < 0 or codesign_str.find(check_strings[1]) < 0:
                    raise Exception("codesign didn't find signature: " + str(codesign_str))

    def _binary(self, string):
        """ should be our name """
        return string == self.name

    def _binary_version(self, version, string):
        """ should be our name """
        return string in [f"{self.name} v{version.major}.{version.minor}", string == "arangobench"]

    def _windows_version(self, version, version_string):
        """ funny windows version should be there """
        return f"{version.major}.{version.minor}.0.{version.patch}" == version_string

    def _company_name(self, version, string):
        """ may find company name """
        # pylint: disable=chained-comparison
        if string == "ArangoDB GmbH":
            return True
        if (version < semver.VersionInfo.parse("3.10.12") or
            (version > semver.VersionInfo.parse("3.11.0") and version < semver.VersionInfo.parse("3.11.5") )):
            return string is None or string == ""
        return False

    def _friendly_name(self, string):
        """ should find friendly name in string """
        return re.match(self.friendly_name, string) is not None

    def _validate_windows_attributes(self, version, enterprise):
        """ validate the windows binary header fields """
        # pylint: disable=import-outside-toplevel disable=too-many-branches
        if not enterprise and self.enterprise:
            return
        if IS_WINDOWS and self.binary_type != "go": # GT-540: remove type comparison, alter versions.
            from win32api import GetFileVersionInfo
            language, codepage = GetFileVersionInfo(str(self.path), '\\VarFileInfo\\Translation')[0]
            for windows_field, hook in PROP_NAMES.items():
                exstr = ''
                check_ok = True
                try:
                    string_file_info = '\\StringFileInfo\\%04X%04X\\%s' % (language, codepage, windows_field)
                    description = GetFileVersionInfo(str(self.path), string_file_info)
                except Exception as ex:
                    description = None
                    exstr = str(ex)
                if description is None:
                    if hook is not None:
                        raise Exception(f"{windows_field} in '{self.path}' expected: to be set to , {hook}, but is None - {exstr}")
                elif hook  == '@binary':
                    check_ok = self._binary(description)
                elif hook == '@binary_version':
                    check_ok = self._binary_version(version, description)
                elif hook  == '@company_name':
                    check_ok = self._company_name(version, description)
                elif hook  == '@windows_version':
                    check_ok = self._windows_version(version, description)
                elif hook  == '@friendly_name':
                    check_ok = self._friendly_name(description)
                else:
                    check_ok = re.match(hook, description) is not None
                if not check_ok:
                    raise Exception(f"{windows_field} in '{self.path}' expected: to be set to , '{hook}', but is {description} - '{exstr}'")

    # pylint: disable=too-many-arguments
    @step
    def check_installed(self, version, enterprise, check_stripped, check_symlink, check_notarized):
        """check all attributes of this file in reality"""
        attach(str(self), "file info")
        if version > self.version_max or version < self.version_min:
            self.check_path(enterprise, False)
            return
        self._validate_windows_attributes(version, enterprise)
        if check_notarized:
            self._validate_notarization(enterprise)
        self.check_path(enterprise)
        if not enterprise and self.enterprise:
            # checks do not need to continue in this case
            return
        if check_stripped:
            self.check_stripped()
        if check_symlink:
            self.check_symlink()

    def check_path(self, enterprise, in_version=True):
        """check whether the file rightfully exists or not"""
        is_there = self.path.is_file()
        if enterprise and self.enterprise:
            if not is_there and in_version:
                raise Exception("Binary missing from enterprise package! " + str(self.path))
        # file must not exist
        if not enterprise and self.enterprise:
            if is_there:
                raise Exception("Enterprise binary found in community package! " + str(self.path))
        elif not is_there and in_version:
            raise Exception("binary was not found! " + str(self.path))

    def check_stripped_mac(self):
        """Checking stripped status of the arangod"""
        time.sleep(1)
        if self.binary_type == "c++":
            # finding out the file size before stripped cmd invoked
            befor_stripped_size = self.path.stat().st_size

            to_file = Path("/tmp/test_whether_stripped")
            shutil.copy(str(self.path), str(to_file))
            # invoke the strip command on file_path
            cmd = ["strip", str(to_file)]
            with subprocess.Popen(cmd, bufsize=-1, stderr=subprocess.PIPE, stdin=subprocess.PIPE) as proc:
                FILE_PIDS.append(str(proc.pid))
                proc.communicate()
                proc.wait()
            # check the size of copied file after stripped
            after_stripped_size = to_file.stat().st_size

            # cleanup temporary file:
            if to_file.is_file():
                to_file.unlink(str(to_file))
            else:
                print("stripped file not found")

            # checking both output size
            return befor_stripped_size == after_stripped_size
        # some go binaries are stripped, some not. We can't test it.
        return self.stripped

    def check_stripped_windows(self):
        """check whether this file is stripped (or not)"""
        output = magic.from_file(str(self.path))
        if output.find("PE32+") < 0:
            raise Exception(f"Strip chinging for file {str(self.path)} returned [{output}]")
        return output.find("(stripped") >= 0

    def check_stripped_linux(self):
        """check whether this file is stripped (or not)"""
        output = magic.from_file(str(self.path))
        if output.find("ELF") < 0:
            raise Exception(f"Strip checking for file {str(self.path)} returned [{output}]")
        if output.find(", stripped") >= 0:
            return True
        if output.find(", not stripped") >= 0:
            return False
        raise Exception(f"Strip checking: parse error for file '{str(self.path)}', unparseable output:  [{output}]")

    @step
    def check_stripped(self):
        """check whether this file is stripped (or not)"""
        is_stripped = True
        if IS_MAC:
            print("")
            # is_stripped = self.check_stripped_mac()
        elif IS_WINDOWS:
            is_stripped = self.check_stripped_windows()
        else:
            is_stripped = self.check_stripped_linux()
            if not is_stripped and self.stripped:

                raise Exception("expected " + str(self.path) + " to be stripped, but it is not stripped")

            if is_stripped and not self.stripped:
                raise Exception("expected " + str(self.path) + " not to be stripped, but it is stripped")

    @step
    def check_symlink(self):
        """check whether the file exists and is a symlink (if)"""
        for link in self.symlink:
            if not link.is_symlink():
                raise Exception("{0} is not a symlink".format(str(link)))
