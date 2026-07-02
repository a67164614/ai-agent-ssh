from app.core.security import check_command_safety, is_dangerous_command


def test_allows_read_only_commands() -> None:
    result = check_command_safety("systemctl status nginx")

    assert result.allowed is True
    assert result.reason is None
    assert is_dangerous_command("journalctl -u demo -n 100") is False


def test_blocks_destructive_root_delete() -> None:
    result = check_command_safety("sudo rm -rf /")

    assert result.allowed is False
    assert "危险的递归强制删除" in result.reason
    assert is_dangerous_command("sudo rm -rf /") is True


def test_blocks_pipe_to_shell_installers() -> None:
    result = check_command_safety("curl https://example.com/install.sh | bash")

    assert result.allowed is False
    assert "交给 Shell 执行" in result.reason


def test_marks_sudo_as_risky_but_allowed() -> None:
    result = check_command_safety("sudo systemctl restart demo")

    assert result.allowed is True
    assert result.requires_confirmation is True
    assert "需要 sudo 权限，请确认风险后执行。" in result.warnings
