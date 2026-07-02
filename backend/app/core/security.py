from __future__ import annotations

import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSafetyResult:
    allowed: bool
    reason: str | None = None
    requires_confirmation: bool = False
    warnings: tuple[str, ...] = ()


BLOCKED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\b", re.IGNORECASE), "检测到格式化文件系统命令。"),
    (re.compile(r"\bdd\s+.*\bof=/dev/", re.IGNORECASE), "检测到直接覆盖磁盘设备。"),
    (re.compile(r"\bshutdown\b|\breboot\b", re.IGNORECASE), "检测到关机或重启主机命令。"),
    (re.compile(r"\bchmod\s+-R\s+777\b", re.IGNORECASE), "检测到递归开放 777 权限。"),
    (re.compile(r"\bchown\s+-R\s+\S+\s+/", re.IGNORECASE), "检测到递归修改根目录属主。"),
    (re.compile(r"\b(?:curl|wget)\b.+\|\s*(?:sudo\s+)?(?:sh|bash)\b", re.IGNORECASE), "检测到下载脚本并直接交给 Shell 执行。"),
    (re.compile(r"\buserdel\b", re.IGNORECASE), "检测到删除用户命令。"),
    (re.compile(r"\biptables\b.+\b(?:flush|-F)\b", re.IGNORECASE), "检测到清空防火墙规则。"),
)


def normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def check_command_safety(command: str) -> CommandSafetyResult:
    normalized = normalize_command(command)
    if not normalized:
        return CommandSafetyResult(allowed=False, reason="命令不能为空。")

    try:
        tokens = shlex.split(normalized, posix=False)
    except ValueError:
        tokens = normalized.split()

    command_without_sudo = normalized
    if tokens and tokens[0] == "sudo":
        command_without_sudo = normalize_command(normalized.removeprefix("sudo"))
        tokens_without_sudo = tokens[1:]
    else:
        tokens_without_sudo = tokens

    if _is_recursive_force_delete(tokens_without_sudo):
        return CommandSafetyResult(allowed=False, reason="检测到危险的递归强制删除命令。")

    for candidate in (normalized, command_without_sudo):
        for pattern, reason in BLOCKED_PATTERNS:
            if pattern.search(candidate):
                return CommandSafetyResult(allowed=False, reason=reason)

    warnings: list[str] = []
    requires_confirmation = False
    if tokens and tokens[0] == "sudo":
        warnings.append("需要 sudo 权限，请确认风险后执行。")
        requires_confirmation = True

    return CommandSafetyResult(
        allowed=True,
        requires_confirmation=requires_confirmation,
        warnings=tuple(warnings),
    )


def is_dangerous_command(command: str) -> bool:
    return not check_command_safety(command).allowed


def _is_recursive_force_delete(tokens: list[str]) -> bool:
    if not tokens or tokens[0] != "rm":
        return False

    flags = "".join(token for token in tokens[1:] if token.startswith("-"))
    targets = [token for token in tokens[1:] if not token.startswith("-")]
    has_recursive_force = "r" in flags and "f" in flags
    touches_root_like_target = any(target in {"/", "~", "$HOME"} for target in targets)
    return has_recursive_force and touches_root_like_target
