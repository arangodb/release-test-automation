""" ArangoDB operator platform tool and license helper """

import requests
import platform
import subprocess
import shlex
import os

from pathlib import Path

TOOL_NAME = "arangodb_operator_platform"
SUPPORTED_OS = "Linux"
ARM64_MACHINE_NAMES = ["arm64", "aarch64"]
AMD64_MACHINE_NAME = "amd64"

CLIENT_ID = os.environ.get("CLIENT_ID", "client_id")
CLIENT_SECRET = os.environ.get("CLIENT_SECRET", "client_secret")

TOOL_PATH = f"{Path(__file__).parent.parent.resolve()}/operator_tool_binary/{TOOL_NAME}"


class LicenseHelper:
    def __init__(self, starter_instance):
        self.starter_instance = starter_instance
        lm_tests_path = Path(__file__).parent.parent.resolve()
        self.inventory_path = f"{lm_tests_path}/inventory/inventory.json"
        self.license_key_path = f"{lm_tests_path}/license_key/license_key.txt"

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

    def generate_license_key(self):
        # create inventory JSON
        command = f'{TOOL_PATH} license inventory --arango.endpoint="{self._get_base_url()}" --arango.authentication Token --arango.token "{self._get_jwt_token()}" {self.inventory_path}'
        LicenseHelper.run_command(command)
        # obtain deployment id
        response = requests.get(f"{self._get_base_url()}/_admin/deployment/id", headers=self._get_auth_header())
        deployment_id = response.json()["id"]
        # generate license key
        command = f'{TOOL_PATH} license generate --deployment.id "{deployment_id}" --inventory {self.inventory_path} --license.client.id "{CLIENT_ID}" --license.client.secret "{CLIENT_SECRET}"'
        with open(self.license_key_path, "w") as f:
            f.write(LicenseHelper.run_command(command).stderr.strip())

    def activate_deployment(self):
        # activate deployment
        command = f'{TOOL_PATH} license activate --arango.endpoint="{self._get_base_url()}" --arango.authentication Token --arango.token "{self._get_jwt_token()}" --license.client.id "{CLIENT_ID}" --license.client.secret "{CLIENT_SECRET}"'
        LicenseHelper.run_command(command)

    def apply_license(self):
        if Path(self.license_key_path).exists():
            with open(self.license_key_path, "r", encoding="utf-8") as f:
                requests.put(
                    f"{self._get_base_url()}/_admin/license", headers=self._get_auth_header(), data=f'"{f.read()}"'
                )

    def get_license_data(self):
        response = requests.get(f"{self._get_base_url()}/_admin/license", headers=self._get_auth_header())
        return LicenseHelper.process_response(response)
