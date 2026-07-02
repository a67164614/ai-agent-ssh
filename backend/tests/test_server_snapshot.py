from __future__ import annotations

from app.services.server_snapshot import parse_linux_snapshot_output


def test_parses_linux_snapshot_output() -> None:
    output = """OS=Ubuntu 22.04.4 LTS
KERNEL=6.5.0-35-generic
CPU_CORES=4
CPU_USAGE=12.50
MEMORY_TOTAL_MB=7936
MEMORY_USED_MB=2048
MEMORY_USAGE=25.81
DISK_TOTAL_GB=98.30
DISK_USED_GB=36.40
DISK_USAGE=37
IP_ADDRESSES=10.0.0.8 172.17.0.1
"""

    snapshot = parse_linux_snapshot_output(output)

    assert snapshot.status == "ok"
    assert snapshot.os_info == "Ubuntu 22.04.4 LTS"
    assert snapshot.kernel == "6.5.0-35-generic"
    assert snapshot.cpu_cores == 4
    assert snapshot.cpu_usage == 12.5
    assert snapshot.memory_total_mb == 7936
    assert snapshot.memory_used_mb == 2048
    assert snapshot.memory_usage == 25.81
    assert snapshot.disk_total_gb == 98.3
    assert snapshot.disk_used_gb == 36.4
    assert snapshot.disk_usage == 37.0
    assert snapshot.ip_addresses == "10.0.0.8 172.17.0.1"


def test_snapshot_parser_marks_missing_output_failed() -> None:
    snapshot = parse_linux_snapshot_output("")

    assert snapshot.status == "failed"
    assert "未返回资源信息" in snapshot.message
