"""Tests for hardware detection."""
import platform
import psutil
import pytest
from localmind.hardware import get_cpu_info, get_ram_info, get_gpu_info, get_storage_info

def test_cpu_info():
    cpu = get_cpu_info()
    assert isinstance(cpu.name, str)
    assert cpu.physical_cores > 0
    assert cpu.logical_cores >= cpu.physical_cores

def test_ram_info():
    ram = get_ram_info()
    assert ram.total_gb > 0
    assert ram.available_gb <= ram.total_gb

def test_storage_info():
    storage = get_storage_info()
    assert storage.total_gb > 0
    assert storage.free_gb >= 0

def test_gpu_info():
    gpus = get_gpu_info()
    # It's okay to have an empty list if no GPU
    assert isinstance(gpus, list)
    for gpu in gpus:
        assert gpu.vram_mb > 0