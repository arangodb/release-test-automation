"""Release Tracker API client"""

from enum import Enum

import requests

# pylint: disable=missing-class-docstring
from requests import HTTPError


class OS(Enum):
    LINUX = "linux"
    WINDOWS = "win"
    MACOS = "macos"


class Arch(Enum):
    ARM = "aarch64"
    X86 = "x86_64"


# pylint: disable=missing-function-docstring, disable=invalid-name
class ReleaseTrackerApiClient:
    """Release Tracker API client"""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        username: str,
        password: str,
        host: str = "release-tracker.arangodb.com",
        port: int = 443,
        protocol: str = "https",
    ):
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.protocol = protocol
        self.api_url = f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}/"

    def _make_request(self, relative_url: str, params=None):
        response = requests.get(url=self.api_url + relative_url, params=params, timeout=120)
        response.raise_for_status()
        return response.json()

    def nightly_branches(self) -> list[str]:
        return self._make_request("nightly-branches")

    def stable_branches(self) -> list[str]:
        return self._make_request("stable-branches")

    def releases_for_branch(self, branch: str, os: OS = None, arch: Arch = None) -> list[str]:
        url = f"branches/{branch}/releases"
        params = {}
        if os:
            params["os"] = os.value
        if arch:
            params["arch"] = arch.value
        return self._make_request(url, params)

    def latest_release(self, branch: str, os: OS = None, arch: Arch = None) -> str:
        url = f"branches/{branch}/latest-release"
        params = {}
        if os:
            params["os"] = os.value
        if arch:
            params["arch"] = arch.value
        return self._make_request(url, params)

    def get_latest_release_if_any(self, branch: str, os: OS = None, arch: Arch = None) -> str:
        try:
            return self.latest_release(branch, os, arch)
        except HTTPError as error:
            if error.response.status_code == 404:
                return None
            raise

    def releases_for_all_branches(self, os: OS = None, arch: Arch = None) -> str:
        url = "list-releases-for-stable-branches"
        params = {}
        if os:
            params["os"] = os.value
        if arch:
            params["arch"] = arch.value
        return self._make_request(url, params)

    def nightly_builds(self, os: OS = None, arch: Arch = None) -> str:
        url = "list-latest-nightly-builds"
        params = {}
        if os:
            params["os"] = os.value
        if arch:
            params["arch"] = arch.value
        return self._make_request(url, params)

    def latest_nightly_for_branch(self, branch: str, os: OS = None, arch: Arch = None) -> str:
        url = f"branches/{branch}/get-latest-nightly-build"
        params = {}
        if os:
            params["os"] = os.value
        if arch:
            params["arch"] = arch.value
        return self._make_request(url, params)

    def get_latest_nightly_if_any(self, branch: str, os: OS = None, arch: Arch = None) -> str:
        try:
            return self.latest_nightly_for_branch(branch, os, arch)
        except HTTPError as error:
            if error.response.status_code == 404:
                return None
            raise
