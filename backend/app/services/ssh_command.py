from __future__ import annotations

import asyncio
import shlex
import socket
from pathlib import PurePosixPath

import asyncssh


class SshCommandError(RuntimeError):
    """SSH 命令执行失败，错误信息已转为中文。"""


def run_server_command(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
    command: str,
    working_directory: str | None = None,
    timeout: int = 60,
) -> tuple[int, str, str]:
    return asyncio.run(
        _run_server_command(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            command=command,
            working_directory=working_directory,
            timeout=timeout,
        )
    )


def upload_file_to_server(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
    local_path: str,
    remote_directory: str,
    remote_filename: str,
    timeout: int = 120,
) -> str:
    return asyncio.run(
        _upload_file_to_server(
            host=host,
            port=port,
            username=username,
            password=password,
            private_key=private_key,
            local_path=local_path,
            remote_directory=remote_directory,
            remote_filename=remote_filename,
            timeout=timeout,
        )
    )


async def _run_server_command(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
    command: str,
    working_directory: str | None,
    timeout: int,
) -> tuple[int, str, str]:
    try:
        async with await _connect(host, port, username, password, private_key) as connection:
            result = await connection.run(_wrap_command(command, working_directory), check=False, timeout=timeout)
            return int(result.exit_status or 0), result.stdout or "", result.stderr or ""
    except (asyncio.TimeoutError, TimeoutError) as error:
        raise SshCommandError("SSH 命令执行超时。") from error
    except asyncssh.PermissionDenied as error:
        raise SshCommandError("SSH 认证失败，请检查用户名、密码或私钥。") from error
    except asyncssh.KeyImportError as error:
        raise SshCommandError("SSH 私钥格式不正确。") from error
    except (OSError, socket.gaierror) as error:
        raise SshCommandError("无法连接到服务器，请检查主机地址、端口和防火墙。") from error
    except asyncssh.Error as error:
        raise SshCommandError(f"SSH 执行失败：{error}") from error


async def _upload_file_to_server(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
    local_path: str,
    remote_directory: str,
    remote_filename: str,
    timeout: int,
) -> str:
    try:
        async with await _connect(host, port, username, password, private_key) as connection:
            await asyncio.wait_for(connection.run(f"mkdir -p {shlex.quote(remote_directory)}", check=True), timeout=timeout)
            remote_path = str(PurePosixPath(remote_directory) / PurePosixPath(remote_filename).name)
            async with connection.start_sftp_client() as sftp:
                await asyncio.wait_for(sftp.put(local_path, remote_path), timeout=timeout)
            return remote_path
    except (asyncio.TimeoutError, TimeoutError) as error:
        raise SshCommandError("上传服务包到服务器超时。") from error
    except asyncssh.PermissionDenied as error:
        raise SshCommandError("SSH 认证失败，无法上传服务包。") from error
    except asyncssh.KeyImportError as error:
        raise SshCommandError("SSH 私钥格式不正确，无法上传服务包。") from error
    except (OSError, socket.gaierror) as error:
        raise SshCommandError("无法连接到服务器，服务包未上传。") from error
    except asyncssh.Error as error:
        raise SshCommandError(f"上传服务包失败：{error}") from error


async def _connect(
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
) -> asyncssh.SSHClientConnection:
    client_keys = [asyncssh.import_private_key(private_key)] if private_key else None
    return await asyncssh.connect(
        host,
        port=port,
        username=username,
        password=password,
        client_keys=client_keys,
        known_hosts=None,
        login_timeout=8,
    )


def _wrap_command(command: str, working_directory: str | None) -> str:
    if not working_directory:
        return command
    return f"cd {shlex.quote(working_directory)} && {command}"

