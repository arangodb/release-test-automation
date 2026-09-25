""" RBAC and operator tools helper class """

import json
import hmac
import hashlib
import base64
import requests
import platform
import subprocess
import shlex
import os

from time import sleep
from pathlib import Path

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

RBAC_SERVICE_START_DELAY = 5

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
        return subprocess.Popen(shlex.split(command), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def delay_execution(delay=RBAC_SERVICE_START_DELAY):
        sleep(delay)

    @staticmethod
    def build_operator(operator_dir_path):
        """builds operator in container and copies binaries to specified folder"""
        tool_path = f"{operator_dir_path}/{OPERATOR_TOOL_NAME}"
        if not Path(tool_path).exists():
            print("arangodb operator binaries were not found locally - need to build them...")
            latest_release_url = "https://api.github.com/repos/arangodb/kube-arangodb/releases/latest"
            release_data = requests.get(latest_release_url, timeout=REQUEST_TIMEOUT).json()
            operator_version = release_data["tarball_url"].split("/")[-1]
            print(f"latest operator release is '{operator_version}'")
            current_machine = (
                ARM64_MACHINE_NAMES[0] if platform.machine().lower() in ARM64_MACHINE_NAMES else AMD64_MACHINE_NAME
            )
            make_target = "bin" if current_machine == AMD64_MACHINE_NAME else "bin-all"
            docker_build_command = f"docker build --network=host --build-arg USERNAME=$(whoami) --build-arg OPERATOR_VER={operator_version} -t kube-operator:rta ."
            print("building the operator image...")
            print(f"{Path(__file__).parent.parent.resolve()}/operator_docker/")
            subprocess.run(
                docker_build_command,
                shell=True,
                cwd=f"{Path(__file__).parent.parent.resolve()}/operator_docker/",
                # capture_output=True,
                # text=True,
            )
            docker_run_command = f"docker run -it --network=host -e COMMAND={make_target} kube-operator:rta"
            print("building the operator in container...")
            subprocess.run(docker_run_command, shell=True) # , capture_output=True, text=True)
            print(f"copying the operator binaries from container to '{operator_dir_path}' dir...")
            docker_cp_command_1 = f"docker cp $(docker ps -alq):/app/kube-arangodb-{operator_version}/bin/{SUPPORTED_OS.lower()}/{current_machine}/{OPERATOR_TOOL_NAME} {operator_dir_path}"
            subprocess.run(docker_cp_command_1, shell=True)
            docker_cp_command_2 = f"docker cp $(docker ps -alq):/app/kube-arangodb-{operator_version}/bin/{SUPPORTED_OS.lower()}/{current_machine}/{OPERATOR_INTEGRATION_TOOL_NAME} {operator_dir_path}"
            subprocess.run(docker_cp_command_2, shell=True)

    @step
    def start_operator_services(self, arangod_url):
        start_sidecar_command = f'{self.sidecar_tool_path} sidecar --arangodb.endpoint="{arangod_url}" --sidecar.auth="{self.jwt_dir_path}" --sidecar.auth.mode="{SIDECAR_AUTH_MODE}" --sidecar.address="{SIDECAR_GRPC}" --sidecar.gateway.address="{SIDECAR_GATEWAY}" --sidecar.health.address="{SIDECAR_HEALTH}" --sidecar.unix.enabled=false --log.level="trace"'  # > {self.operator_dir_path / "sidecar.log"}'
        print("starting the authorization sidecar...")
        self.auth_sidecar = RBACHelper.run_command(start_sidecar_command)
        RBACHelper.delay_execution()
        print("starting the authorization integration service...")
        os.environ["CENTRAL_INTEGRATION_SERVICE_ADDRESS"] = SIDECAR_GRPC
        start_integration_svc_command = f'{self.integration_tool_path} --database.auth="{self.jwt_dir_path}" --integration.authorization.v1 --integration.authorization.v1.type="{INTEGRATION_SVC_MODE}" --integration.authentication.v1 --integration.authentication.v1.path="{self.jwt_dir_path}" --services.address="{INTEGRATION_GRPC}" --services.gateway.address="{INTEGRATION_GATEWAY}"'  # > {self.operator_dir_path / "integration.log"}'
        self.auth_integration_svc = RBACHelper.run_command(start_integration_svc_command)
        RBACHelper.delay_execution()

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
