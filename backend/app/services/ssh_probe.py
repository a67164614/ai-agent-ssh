from __future__ import annotations

import asyncio
import socket

import asyncssh


async def probe_ssh_connection(
    *,
    host: str,
    port: int,
    username: str,
    password: str | None,
    private_key: str | None,
) -> tuple[bool, str]:
    try:
        client_keys = [asyncssh.import_private_key(private_key)] if private_key else None
        async with asyncssh.connect(
            host,
            port=port,
            username=username,
            password=password,
            client_keys=client_keys,
            known_hosts=None,
            login_timeout=8,
        ):
            return True, "SSH 连接成功。"
    except (asyncio.TimeoutError, TimeoutError):
        return False, "SSH 连接失败：连接超时，请检查主机地址、端口和防火墙。"
    except asyncssh.PermissionDenied:
        return False, "SSH 连接失败：用户名、密码或私钥认证失败。"
    except asyncssh.KeyImportError:
        return False, "SSH 连接失败：私钥格式不正确。"
    except (OSError, socket.gaierror):
        return False, "SSH 连接失败：无法连接到服务器，请检查主机地址和端口。"
    except asyncssh.Error as error:
        return False, f"SSH 连接失败：{error}"
