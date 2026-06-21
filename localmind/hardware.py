"""Hardware detection using psutil and optionally GPUtil."""
from __future__ import annotations
import platform
import psutil
from typing import List, Optional
from .models import CPUInfo, RAMInfo, GPUInfo, StorageInfo, HardwareReport
from .utils import log_warning


def get_cpu_info() -> CPUInfo:
    """Return CPU information."""
    freq = psutil.cpu_freq()
    return CPUInfo(
        name=platform.processor() or "Unknown CPU",
        physical_cores=psutil.cpu_count(logical=False) or 1,
        logical_cores=psutil.cpu_count(logical=True) or 1,
        max_frequency_mhz=freq.max if freq else 0.0,
    )


def get_ram_info() -> RAMInfo:
    """Return RAM info in GB."""
    mem = psutil.virtual_memory()
    return RAMInfo(
        total_gb=round(mem.total / (1024 ** 3), 2),
        available_gb=round(mem.available / (1024 ** 3), 2),
    )


def get_gpu_info() -> List[GPUInfo]:
    """Return a list of GPUs, if any. Uses GPUtil when available."""
    gpus: List[GPUInfo] = []
    try:
        import GPUtil
        gpu_list = GPUtil.getGPUs()
        for gpu in gpu_list:
            gpus.append(GPUInfo(
                name=gpu.name,
                vram_mb=gpu.memoryTotal,
                driver_version=gpu.driver,
            ))
    except ImportError:
        log_warning("GPUtil not installed – skipping GPU detection.")
    except Exception as e:
        log_warning(f"GPU detection failed: {e}")
    return gpus


def get_storage_info() -> StorageInfo:
    """Return info about the root filesystem."""
    usage = psutil.disk_usage('/')
    return StorageInfo(
        total_gb=round(usage.total / (1024 ** 3), 2),
        used_gb=round(usage.used / (1024 ** 3), 2),
        free_gb=round(usage.free / (1024 ** 3), 2),
    )


def get_full_report() -> HardwareReport:
    """Compile a complete hardware report."""
    return HardwareReport(
        os=f"{platform.system()} {platform.release()}",
        cpu=get_cpu_info(),
        ram=get_ram_info(),
        gpus=get_gpu_info(),
        storage=get_storage_info(),
    )