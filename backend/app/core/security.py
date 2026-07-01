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
    (re.compile(r"\bmkfs(?:\.[a-z0-9]+)?\b", re.IGNORECASE), "filesystem formatting"),
    (re.compile(r"\bdd\s+.*\bof=/dev/", re.IGNORECASE), "raw disk overwrite"),
    (re.compile(r"\bshutdown\b|\breboot\b", re.IGNORECASE), "host shutdown or reboot"),
    (re.compile(r"\bchmod\s+-R\s+777\b", re.IGNORECASE), "recursive world-writable chmod"),
    (re.compile(r"\bchown\s+-R\s+\S+\s+/", re.IGNORECASE), "recursive root ownership change"),
    (re.compile(r"\b(?:curl|wget)\b.+\|\s*(?:sudo\s+)?(?:sh|bash)\b", re.IGNORECASE), "pipe to shell installer"),
    (re.compile(r"\buserdel\b", re.IGNORECASE), "user deletion"),
    (re.compile(r"\biptables\b.+\b(?:flush|-F)\b", re.IGNORECASE), "firewall flush"),
)


def normalize_command(command: str) -> str:
    return " ".join(command.strip().split())


def check_command_safety(command: str) -> CommandSafetyResult:
    normalized = normalize_command(command)
    if not normalized:
        return CommandSafetyResult(allowed=False, reason="empty command")

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
        return CommandSafetyResult(allowed=False, reason="rm -rf / style deletion")

    for candidate in (normalized, command_without_sudo):
        for pattern, reason in BLOCKED_PATTERNS:
            if pattern.search(candidate):
                return CommandSafetyResult(allowed=False, reason=reason)

    warnings: list[str] = []
    requires_confirmation = False
    if tokens and tokens[0] == "sudo":
        warnings.append("sudo")
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
