from __future__ import annotations
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

try:
    import psutil  # type: ignore
except Exception:
    psutil = None  # type: ignore

@dataclass
class DiskInfo:
    mount: str
    total_gb: Optional[float]
    used_gb: Optional[float]
    free_gb: Optional[float]
    used_percent: Optional[float]

@dataclass
class MemoryInfo:
    total_gb: Optional[float]
    used_gb: Optional[float]
    free_gb: Optional[float]
    used_percent: Optional[float]

@dataclass
class CPUInfo:
    cores_logical: Optional[int]
    load_percent: Optional[float]

@dataclass
class ServiceStatus:
    name: str
    status: str  # active/inactive/running/stopped/unknown/error
    detail: str = ""

@dataclass
class HealthSnapshot:
    timestamp: str
    hostname: str
    os: str
    os_version: str
    disks: List[DiskInfo]
    memory: MemoryInfo
    cpu: CPUInfo
    services: List[ServiceStatus]

def _bytes_to_gb(b: float) -> float:
    return round(b / (1024 ** 3), 2)

def get_disks() -> List[DiskInfo]:
    disks: List[DiskInfo] = []
    if psutil is not None:
        try:
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    disks.append(DiskInfo(
                        mount=part.mountpoint,
                        total_gb=_bytes_to_gb(usage.total),
                        used_gb=_bytes_to_gb(usage.used),
                        free_gb=_bytes_to_gb(usage.free),
                        used_percent=round(float(usage.percent), 2),
                    ))
                except Exception:
                    continue
        except Exception:
            disks = []

    if not disks:
        try:
            usage = shutil.disk_usage(Path("/"))
            total = usage.total
            used = total - usage.free
            disks.append(DiskInfo(
                mount=str(Path("/")),
                total_gb=_bytes_to_gb(total),
                used_gb=_bytes_to_gb(used),
                free_gb=_bytes_to_gb(usage.free),
                used_percent=round((used / total) * 100, 2) if total else None,
            ))
        except Exception:
            disks.append(DiskInfo(mount="unknown", total_gb=None, used_gb=None, free_gb=None, used_percent=None))
    return disks

def get_memory() -> MemoryInfo:
    if psutil is not None:
        try:
            vm = psutil.virtual_memory()
            return MemoryInfo(
                total_gb=_bytes_to_gb(vm.total),
                used_gb=_bytes_to_gb(vm.used),
                free_gb=_bytes_to_gb(vm.available),
                used_percent=round(float(vm.percent), 2),
            )
        except Exception:
            pass

    try:
        if Path("/proc/meminfo").exists():
            data = Path("/proc/meminfo").read_text(encoding="utf-8", errors="ignore").splitlines()
            kv = {}
            for line in data:
                if ":" in line:
                    k, v = line.split(":", 1)
                    kv[k.strip()] = v.strip()

            def _kb_to_gb(kb: float) -> float:
                return round((kb * 1024) / (1024 ** 3), 2)

            mem_total_kb = float(kv.get("MemTotal", "0 kB").split()[0])
            mem_avail_kb = float(kv.get("MemAvailable", "0 kB").split()[0])
            total_gb = _kb_to_gb(mem_total_kb) if mem_total_kb else None
            free_gb = _kb_to_gb(mem_avail_kb) if mem_avail_kb else None
            used_gb = round(total_gb - free_gb, 2) if (total_gb is not None and free_gb is not None) else None
            used_pct = round((used_gb / total_gb) * 100, 2) if (used_gb is not None and total_gb) else None
            return MemoryInfo(total_gb=total_gb, used_gb=used_gb, free_gb=free_gb, used_percent=used_pct)
    except Exception:
        pass

    return MemoryInfo(total_gb=None, used_gb=None, free_gb=None, used_percent=None)

def get_cpu() -> CPUInfo:
    if psutil is not None:
        try:
            cores = psutil.cpu_count(logical=True)
            load = psutil.cpu_percent(interval=0.5)
            return CPUInfo(cores_logical=cores, load_percent=round(float(load), 2))
        except Exception:
            pass
    try:
        cores = os.cpu_count()
    except Exception:
        cores = None
    return CPUInfo(cores_logical=cores, load_percent=None)

def _is_windows() -> bool:
    return platform.system().lower() == "windows"

def _has_systemctl() -> bool:
    return shutil.which("systemctl") is not None

def check_services(service_names: List[str]) -> List[ServiceStatus]:
    statuses: List[ServiceStatus] = []
    if not service_names:
        return statuses

    if _is_windows() and psutil is not None:
        for name in service_names:
            try:
                svc = psutil.win_service_get(name)  # type: ignore[attr-defined]
                info = svc.as_dict()
                stat = info.get("status") or "unknown"
                statuses.append(ServiceStatus(name=name, status=str(stat), detail=str(info.get("display_name") or "")))
            except Exception as e:
                statuses.append(ServiceStatus(name=name, status="error", detail=str(e)))
        return statuses

    if _has_systemctl():
        for name in service_names:
            try:
                cp = subprocess.run(
                    ["systemctl", "is-active", name],
                    capture_output=True,
                    text=True,
                    timeout=3,
                )
                out = (cp.stdout or "").strip()
                err = (cp.stderr or "").strip()
                status = out if out else ("error" if cp.returncode != 0 else "unknown")
                statuses.append(ServiceStatus(name=name, status=status, detail=err))
            except Exception as e:
                statuses.append(ServiceStatus(name=name, status="error", detail=str(e)))
        return statuses

    for name in service_names:
        statuses.append(ServiceStatus(name=name, status="unknown", detail="service check not supported on this OS"))
    return statuses

def collect_health_snapshot(service_names: List[str]) -> HealthSnapshot:
    now = datetime.now().isoformat(timespec="seconds")
    hostname = platform.node() or "unknown-host"
    os_name = platform.system() or "unknown"
    os_ver = platform.version() or platform.release() or "unknown"
    return HealthSnapshot(
        timestamp=now,
        hostname=hostname,
        os=os_name,
        os_version=os_ver,
        disks=get_disks(),
        memory=get_memory(),
        cpu=get_cpu(),
        services=check_services(service_names),
    )
