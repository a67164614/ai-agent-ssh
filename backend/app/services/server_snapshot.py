from __future__ import annotations

from dataclasses import dataclass


SNAPSHOT_COMMAND = r"""sh -lc '
OS=$(. /etc/os-release 2>/dev/null && echo "${PRETTY_NAME:-$NAME}" || uname -s)
KERNEL=$(uname -r 2>/dev/null || echo "")
CPU_CORES=$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 0)
CPU_USAGE=$(LC_ALL=C top -bn1 2>/dev/null | awk -F"," "/Cpu|%Cpu/ {gsub(/[^0-9.]/,\"\",$4); if ($4 != \"\") printf \"%.2f\", 100 - $4; exit}")
MEMORY=$(awk "/MemTotal/ {total=\$2} /MemAvailable/ {avail=\$2} END {used=total-avail; if (total > 0) printf \"%d %d %.2f\", total/1024, used/1024, used*100/total; else printf \"0 0 0\"}" /proc/meminfo 2>/dev/null)
DISK=$(df -BG / 2>/dev/null | awk "NR==2 {gsub(/G/,\"\",\$2); gsub(/G/,\"\",\$3); gsub(/%/,\"\",\$5); printf \"%s %s %s\", \$2, \$3, \$5}")
IPS=$(hostname -I 2>/dev/null | xargs)
echo "OS=$OS"
echo "KERNEL=$KERNEL"
echo "CPU_CORES=$CPU_CORES"
echo "CPU_USAGE=${CPU_USAGE:-0}"
echo "$MEMORY" | awk "{print \"MEMORY_TOTAL_MB=\"\$1\"\nMEMORY_USED_MB=\"\$2\"\nMEMORY_USAGE=\"\$3}"
echo "$DISK" | awk "{print \"DISK_TOTAL_GB=\"\$1\"\nDISK_USED_GB=\"\$2\"\nDISK_USAGE=\"\$3}"
echo "IP_ADDRESSES=$IPS"
'"""


@dataclass(frozen=True)
class ParsedServerSnapshot:
    status: str
    cpu_usage: float | None = None
    cpu_cores: int | None = None
    memory_usage: float | None = None
    memory_total_mb: int | None = None
    memory_used_mb: int | None = None
    disk_usage: float | None = None
    disk_total_gb: float | None = None
    disk_used_gb: float | None = None
    os_info: str | None = None
    kernel: str | None = None
    ip_addresses: str | None = None
    message: str | None = None


def parse_linux_snapshot_output(output: str) -> ParsedServerSnapshot:
    if not output.strip():
        return ParsedServerSnapshot(status="failed", message="服务器未返回资源信息。")

    values = _parse_key_values(output)
    if not values:
        return ParsedServerSnapshot(status="failed", message="服务器资源信息格式不正确。")

    return ParsedServerSnapshot(
        status="ok",
        cpu_usage=_float_or_none(values.get("CPU_USAGE")),
        cpu_cores=_int_or_none(values.get("CPU_CORES")),
        memory_usage=_float_or_none(values.get("MEMORY_USAGE")),
        memory_total_mb=_int_or_none(values.get("MEMORY_TOTAL_MB")),
        memory_used_mb=_int_or_none(values.get("MEMORY_USED_MB")),
        disk_usage=_float_or_none(values.get("DISK_USAGE")),
        disk_total_gb=_float_or_none(values.get("DISK_TOTAL_GB")),
        disk_used_gb=_float_or_none(values.get("DISK_USED_GB")),
        os_info=values.get("OS") or None,
        kernel=values.get("KERNEL") or None,
        ip_addresses=values.get("IP_ADDRESSES") or None,
        message="服务器资源快照采集成功。",
    )


def _parse_key_values(output: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in output.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _float_or_none(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _int_or_none(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except ValueError:
        return None

