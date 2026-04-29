""" ArangoDB operator platform tool and license helper """

import requests
import platform
import subprocess
import shlex
import os

from pathlib import Path

from reporting.reporting_utils import step

TOOL_NAME = "arangodb_operator_platform"
SUPPORTED_OS = "Linux"
ARM64_MACHINE_NAMES = ["arm64", "aarch64"]
AMD64_MACHINE_NAME = "amd64"

DEFAULT_CLIENT_ID = "my-client-id"
DEFAULT_CLIENT_SECRET = "111aaa22-333b-4ccc-d5dd-e678ffff9012"
CLIENT_ID = os.environ.get("CLIENT_ID", DEFAULT_CLIENT_ID)
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", DEFAULT_CLIENT_SECRET)

TOOL_PATH = f"{Path(__file__).parent.parent.resolve()}/operator_tool_binary/{TOOL_NAME}"
INVENTORY_PATH = f"{Path(__file__).parent.parent.resolve()}/inventory/inventory.json"
LICENSE_KEY_PATH = f"{Path(__file__).parent.parent.resolve()}/license_key/license_key.txt"


class LicenseHelper:
    def __init__(self, starter_instance):
        self.starter_instance = starter_instance

    def _get_base_url(self):
        fe_instance = [instance for instance in self.starter_instance.all_instances if instance.is_frontend()][0]
        return self.starter_instance.get_http_protocol() + "://" + fe_instance.get_public_plain_url()

    def _get_jwt_token(self):
        return str(self.starter_instance.get_jwt_header())

    def _get_auth_header(self):
        return {"Authorization": "Bearer " + self._get_jwt_token()}

    @staticmethod
    def process_response(response):
        try:
            json_payload = response.json()
        except requests.exceptions.JSONDecodeError:
            json_payload = {}
        return {"code": response.status_code, "json": json_payload}

    @staticmethod
    def run_command(command):
        return subprocess.run(shlex.split(command), capture_output=True, text=True)

    @staticmethod
    def download_operator_platform_tool():
        """downloads operator platform tool for the current platform"""
        if not Path(TOOL_PATH).exists():
            latest_release_url = "https://api.github.com/repos/arangodb/kube-arangodb/releases/latest"
            release_data = requests.get(latest_release_url).json()
            current_machine = (
                ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
            )
            asset_name = f"{TOOL_NAME}_{SUPPORTED_OS.lower()}_{current_machine}"
            download_url = [
                asset["browser_download_url"] for asset in release_data["assets"] if asset["name"] == asset_name
            ][0]
            response = requests.get(download_url, stream=True)
            with open(TOOL_PATH, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
        # ensure operator platform tool is executable
        command = f"chmod +x {TOOL_PATH}"
        LicenseHelper.run_command(command)

    def generate_license_key(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        """gather inventory and deployment data and generate a license key with operator platform tool"""
        # create inventory JSON
        command = f'{TOOL_PATH} license inventory --arango.endpoint="{self._get_base_url()}" --arango.authentication Token --arango.token "{self._get_jwt_token()}" {INVENTORY_PATH}'
        LicenseHelper.run_command(command)
        # obtain deployment id
        response = requests.get(f"{self._get_base_url()}/_admin/deployment/id", headers=self._get_auth_header())
        deployment_id = response.json()["id"]
        # generate license key
        command = f'{TOOL_PATH} license generate --deployment.id "{deployment_id}" --inventory {INVENTORY_PATH} --license.client.id "{client_id}" --license.client.secret "{client_secret}"'
        with open(LICENSE_KEY_PATH, "w") as f:
            f.write(LicenseHelper.run_command(command).stderr.strip())

    def activate_deployment(self, client_id=CLIENT_ID, client_secret=CLIENT_SECRET):
        """activate deployment with operator platform tool"""
        # activate deployment
        command = f'{TOOL_PATH} license activate --arango.endpoint="{self._get_base_url()}" --arango.authentication Token --arango.token "{self._get_jwt_token()}" --license.client.id "{client_id}" --license.client.secret "{client_secret}"'
        LicenseHelper.run_command(command)

    @step
    def apply_license(self):
        """apply license using generated license key"""
        if Path(LICENSE_KEY_PATH).exists():
            with open(LICENSE_KEY_PATH, "r", encoding="utf-8") as f:
                requests.put(
                    f"{self._get_base_url()}/_admin/license", headers=self._get_auth_header(), data=f'"{f.read()}"'
                )

    @step
    def get_license_data(self):
        """obtain current license data"""
        response = requests.get(f"{self._get_base_url()}/_admin/license", headers=self._get_auth_header())
        return LicenseHelper.process_response(response)

    @staticmethod
    def cleanup():
        if Path(INVENTORY_PATH).exists():
            os.remove(INVENTORY_PATH)
        if Path(LICENSE_KEY_PATH).exists():
            os.remove(LICENSE_KEY_PATH)
        # deleting operator platform tool after each test suite execution is suboptimal
        # if Path(TOOL_PATH).exists():
        #     os.remove(TOOL_PATH)
