""" RBAC and operator tools helper class """

import json
import hmac
import hashlib
import base64
import requests
import platform
import subprocess
import shlex
import shutil
import os

from time import sleep
from pathlib import Path
from zipfile import ZipFile

from reporting.reporting_utils import step

OPERATOR_TOOL_NAME = "arangodb_operator"
OPERATOR_INTEGRATION_TOOL_NAME = "arangodb_operator_integration"
SUPPORTED_OS = "Linux"
ARM64_MACHINE_NAMES = ["arm64", "aarch64"]
AMD64_MACHINE_NAME = "amd64"
REQUEST_TIMEOUT = 60

SIDECAR_AUTH_MODE = "central-permissive"
SIDECAR_GRPC = "127.0.0.1:8109"
SIDECAR_GATEWAY = "127.0.0.1:8108"
SIDECAR_HEALTH = "127.0.0.1:8107"

INTEGRATION_SVC_MODE = "central"
INTEGRATION_GATEWAY = "127.0.0.1:9192"
INTEGRATION_GRPC = "127.0.0.1:9092"

USER_TYPES = ["superuser", "user"]


class RBACHelper:
    def __init__(self, operator_dir_path, jwt_dir_path):
        self.jwt_dir_path = jwt_dir_path
        self.jwt_secret_path = f"{jwt_dir_path / '-'}"
        self.operator_dir_path = operator_dir_path
        self.sidecar_tool_path = f"{operator_dir_path}/{OPERATOR_TOOL_NAME}"
        self.integration_tool_path = f"{operator_dir_path}/{OPERATOR_INTEGRATION_TOOL_NAME}"
        self.auth_integration_svc = None
        self.auth_sidecar = None
        self.sidecar_url = f"http://{SIDECAR_GATEWAY}"
        self.integration_url = f"http://{INTEGRATION_GATEWAY}"

    @staticmethod
    def b64u(b: bytes) -> str:
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()

    @staticmethod
    def sign(secret: bytes, header: dict, payload: dict) -> str:
        h = RBACHelper.b64u(json.dumps(header, separators=(",", ":")).encode())
        p = RBACHelper.b64u(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{h}.{p}".encode()
        sig = hmac.new(secret, signing_input, hashlib.sha256).digest()
        return f"{h}.{p}.{RBACHelper.b64u(sig)}"

    @staticmethod
    def run_command(command):
        # return subprocess.Popen(shlex.split(command))
        return subprocess.Popen(shlex.split(command), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def run_simple_command(command):
        return subprocess.run(shlex.split(command), capture_output=True, text=True)

    @staticmethod
    def download_operator_binaries(operator_dir_path):
        """downloads operator integration tool for the current platform"""
        tool_path = f"{operator_dir_path}/{OPERATOR_INTEGRATION_TOOL_NAME}"
        if not Path(tool_path).exists():
            latest_release_url = "https://api.github.com/repos/arangodb/kube-arangodb/releases/latest"
            release_data = requests.get(latest_release_url, timeout=REQUEST_TIMEOUT).json()
            current_machine = (
                ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
            )
            asset_name = f"{OPERATOR_INTEGRATION_TOOL_NAME}_{SUPPORTED_OS.lower()}_{current_machine}"
            download_url = [
                asset["browser_download_url"] for asset in release_data["assets"] if asset["name"] == asset_name
            ][0]
            response = requests.get(download_url, stream=True, timeout=REQUEST_TIMEOUT)
            with open(tool_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    f.write(chunk)
        # ensure operator platform tool is executable
        command = f"chmod +x {tool_path}"
        RBACHelper.run_simple_command(command)

    @staticmethod
    def copy_operator_binary(operator_dir_path):
        """unzips and copies operator tool for the current platform to work directory"""
        tool_path = f"{operator_dir_path}/{OPERATOR_TOOL_NAME}"
        if not Path(tool_path).exists():
            current_machine = (
                ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
            )
            bin_name = f"{OPERATOR_TOOL_NAME}_{current_machine}"
            operator_dir_path = f"{Path(__file__).parent.parent.resolve()}/operator_bin/"
            operator_tool_path = f"{operator_dir_path}{bin_name}"
            with ZipFile(f"{operator_tool_path}.zip", "r") as zip_file:
                zip_file.extractall(path=operator_dir_path)
                shutil.move(operator_tool_path, tool_path)
        # ensure operator platform tool is executable
        command = f"chmod +x {tool_path}"
        RBACHelper.run_simple_command(command)

    @staticmethod
    def copy_operator_integration_binary(operator_dir_path):
        """unzips and copies operator tool for the current platform to work directory"""
        tool_path = f"{operator_dir_path}/{OPERATOR_INTEGRATION_TOOL_NAME}"
        if not Path(tool_path).exists():
            current_machine = (
                ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
            )
            bin_name = f"{OPERATOR_INTEGRATION_TOOL_NAME}_{current_machine}"
            operator_dir_path = f"{Path(__file__).parent.parent.resolve()}/operator_bin/"
            operator_tool_path = f"{operator_dir_path}{bin_name}"
            with ZipFile(f"{operator_tool_path}.zip", "r") as zip_file:
                zip_file.extractall(path=operator_dir_path)
                shutil.move(operator_tool_path, tool_path)
        # ensure operator platform tool is executable
        command = f"chmod +x {tool_path}"
        RBACHelper.run_simple_command(command)

    @step
    def start_operator_services(self, arangod_url):
        start_sidecar_command = f'{self.sidecar_tool_path} sidecar --arangodb.endpoint="{arangod_url}" --sidecar.auth="{self.jwt_dir_path}" --sidecar.auth.mode="{SIDECAR_AUTH_MODE}" --sidecar.address="{SIDECAR_GRPC}" --sidecar.gateway.address="{SIDECAR_GATEWAY}" --sidecar.health.address="{SIDECAR_HEALTH}" --sidecar.unix.enabled=false --log.level="trace"'  # > {self.operator_dir_path / "sidecar.log"}'
        print("starting the authorization sidecar...")
        self.auth_sidecar = RBACHelper.run_command(start_sidecar_command)
        sleep(5)
        print("starting the authorization integration service...")
        os.environ["CENTRAL_INTEGRATION_SERVICE_ADDRESS"] = SIDECAR_GRPC
        start_integration_svc_command = f'{self.integration_tool_path} --database.auth="{self.jwt_dir_path}" --integration.authorization.v1 --integration.authorization.v1.type="{INTEGRATION_SVC_MODE}" --integration.authentication.v1 --integration.authentication.v1.path="{self.jwt_dir_path}" --services.address="{INTEGRATION_GRPC}" --services.gateway.address="{INTEGRATION_GATEWAY}"'  # > {self.operator_dir_path / "integration.log"}'
        self.auth_integration_svc = RBACHelper.run_command(start_integration_svc_command)
        sleep(5)

    def generate_token(self, user_type, user_name=""):
        header = {"alg": "HS256", "typ": "JWT"}
        if user_type == USER_TYPES[0]:
            payload = {"iss": "arangodb", "server_id": "test"}
        else:
            payload = {"iss": "arangodb", "preferred_username": user_name}
        with open(self.jwt_secret_path, "rb") as secret_file:
            return RBACHelper.sign(secret_file.read(), header, payload)

    def stop_operator_services(self):
        self.auth_sidecar.terminate()
        self.auth_integration_svc.terminate()
