"""Client to handle connections and actions executed against a remote host."""
# "Inspired" by: https://github.com/hackersandslackers/paramiko-tutorial
from os import system
from typing import List

from paramiko import AutoAddPolicy, RSAKey, SSHClient, agent
from paramiko.auth_handler import AuthenticationException, SSHException
from scp import SCPClient, SCPException

# from log import LOGGER


class RemoteClient:
    """Client to interact with a remote host via SSH & SCP."""
    # pylint: disable=too-many-arguments disable=broad-except
    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        ssh_key_filepath: str,
        remote_path: str,
    ):
        self.host = host
        self.user = user
        self.password = password
        self.ssh_key_filepath = ssh_key_filepath
        self.remote_path = remote_path
        self.client = None
        self.ssh_key = None
        self._upload_ssh_key()

    @property
    def connection(self):
        """Open SSH connection to remote host."""
        try:
            client = SSHClient()
            client.load_system_host_keys()
            # client.set_missing_host_key_policy(AutoAddPolicy())
            client.connect(
                self.host,
                username=self.user,
                password=self.password,
                # key_filename=self.ssh_key_filepath,
                timeout=5000,
            )
            agent.AgentRequestHandler(client.get_transport().open_session())
            return client
        except AuthenticationException as exc:
            print(
                f"AuthenticationException occurred; did you remember to generate an SSH key? {exc}"
            )
            raise exc
        except Exception as exc:
            print(f"Unexpected error occurred while connecting to host: {exc}")
            raise exc

    @property
    def scp(self) -> SCPClient:
        """ upload files using the scp client """
        conn = self.connection
        return SCPClient(conn.get_transport())

    def _get_ssh_key(self):
        """Fetch locally stored SSH key."""
        try:
            self.ssh_key = RSAKey.from_private_key_file(self.ssh_key_filepath)
            print(f"Found SSH key at self {self.ssh_key_filepath}")
            return self.ssh_key
        except SSHException as exc:
            print(f"SSHException while getting SSH key: {exc}")
            raise exc
        except Exception as exc:
            print(f"Unexpected error while getting SSH key: {exc}")
            raise exc

    def _upload_ssh_key(self):
        try:
            system(
                f"ssh-copy-id -i {self.ssh_key_filepath}.pub {self.user}@{self.host}>/dev/null 2>&1"
            )
            print(f"{self.ssh_key_filepath} uploaded to {self.host}")
        except FileNotFoundError as exc:
            print(f"FileNotFoundError while uploading SSH key: {exc}")
            raise exc
        except Exception as exc:
            print(f"Unexpected error while uploading SSH key: {exc}")
            raise exc

    def disconnect(self):
        """Close SSH & SCP connection."""
        if self.connection:
            self.client.close()
        if self.scp:
            self.scp.close()

    def bulk_upload(self, filepaths: List[str]):
        """
        Upload multiple files to a remote directory.

        :param List[str] filepaths: List of local files to be uploaded.
        """
        try:
            self.scp.put(filepaths, remote_path=self.remote_path, recursive=True)
            print(
                f"Finished uploading {len(filepaths)} files to {self.remote_path} on {self.host}"
            )
        except SCPException as exc:
            print(f"SCPException during bulk upload: {exc}")
            raise exc
        except Exception as exc:
            print(f"Unexpected exception during bulk upload: {exc}")
            raise exc

    def download_file(self, filepath: str):
        """
        Download file from remote host.

        :param str filepath: Path to file hosted on remote server to fetch.
        """
        self.scp.get(filepath)

    def execute_commands(self, commands: List[str]):
        """
        Execute multiple commands in succession.

        :param List[str] commands: List of unix commands as strings.
        """
        for cmd in commands:
            print(cmd)
            _, stdout, _ = self.connection.exec_command(cmd)
            stdout.channel.recv_exit_status()
            response = stdout.readlines()
            for line in response:
                print(
                    f"INPUT: {cmd}\n \
                    OUTPUT: {line}"
                )
