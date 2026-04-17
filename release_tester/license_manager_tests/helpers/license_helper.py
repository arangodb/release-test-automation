""" ArangoDB operator platform tool helper """

import requests
import platform
import subprocess
import shlex

from pathlib import Path


SUPPORTED_OS = "Linux"
TOOL_NAME = "arangodb_operator_platform"
CLIENT_ID = "client_id"
CLIENT_SECRET = "client_secret"
ARM64_MACHINE_NAMES = ["arm64", "aarch64"]
AMD64_MACHINE_NAME = "amd64"


class LicenseHelper:
    def __init__(self, starter_instance):
        self.starter_instance = starter_instance
        self.machine = (
            ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
        )
        lm_tests_path = Path(__file__).parent.parent.resolve()
        self.tool_path = f"{lm_tests_path}/operator_tool_binary/{TOOL_NAME}"
        self.inventory_path = f"{lm_tests_path}/inventory/inventory.json"
        self.license_key_path = f"{lm_tests_path}/license_key/license_key.txt"

    def _get_base_url(self):
        fe_instance = [instance for instance in self.starter_instance.all_instances if instance.is_frontend()][0]
        return self.starter_instance.get_http_protocol() + "://" + fe_instance.get_public_plain_url()

    @staticmethod
    def _run_command(command):
        subprocess.run(shlex.split(command), stdout=subprocess.PIPE).stdout.decode("utf-8")

    def download_operator_platform_tool(self):
        """downloads operator platform tool for the current platform"""
        if not Path(self.tool_path).exists():
            latest_release_url = "https://api.github.com/repos/arangodb/kube-arangodb/releases/latest"
            release_data = requests.get(latest_release_url).json()
            asset_name = f"{TOOL_NAME}_{SUPPORTED_OS.lower()}_{self.machine}"
            download_url = [
                asset["browser_download_url"] for asset in release_data["assets"] if asset["name"] == asset_name
            ][0]
            response = requests.get(download_url, stream=True)
            with open(self.tool_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)

    def generate_license_key(self):
        # create inventory JSON
        command = f"chmod +x {self.tool_path}"
        LicenseHelper._run_command(command)
        jwt_header = str(self.starter_instance.get_jwt_header())
        command = f'{self.tool_path} license inventory --arango.endpoint="{self._get_base_url()}" --arango.authentication Token --arango.token "{jwt_header}" {self.inventory_path}'
        LicenseHelper._run_command(command)
        # obtain deployment id
        request_headers = {"Authorization": "Bearer " + jwt_header}
        response = requests.get(f"{self._get_base_url()}/_admin/deployment/id", headers=request_headers)
        deployment_id = response.json()["id"]
        print(f"Deployment ID: {deployment_id}")
        # generate license key
        # command = f'{self.tool_path} license generate --deployment.id "{deployment_id}" --inventory {self.inventory_path} --license.client.id "{CLIENT_ID}" --license.client.secret "{CLIENT_SECRET}" 2> {self.license_key_path}'
        # LicenseHelper._run_command(command)

    def apply_license(self):
        with open(self.license_key_path, "r", encoding="utf-8") as f:
            license_key = f.read()
            requests.put(f"{self._get_base_url()}/_admin/license", data=license_key)

    def check_license(self):
        response = requests.get(f"{self._get_base_url()}/_admin/license")
        assert response.status_code == 200
