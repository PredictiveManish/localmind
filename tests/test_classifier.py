"""Tests for machine classification."""
from localmind.models import HardwareReport, CPUInfo, RAMInfo, StorageInfo, GPUInfo
from localmind.classifier import classify_machine

def test_tiny_machine():
    hw = HardwareReport(
        os="Test",
        cpu=CPUInfo(name="x", physical_cores=1, logical_cores=1, max_frequency_mhz=1000),
        ram=RAMInfo(total_gb=4.0, available_gb=2.0),
        gpus=[],
        storage=StorageInfo(total_gb=100, used_gb=50, free_gb=50),
    )
    mc = classify_machine(hw)
    assert mc.tier == "Tiny"
    assert mc.recommended_param_range == "1B-4B"

def test_enthusiast_machine():
    hw = HardwareReport(
        os="Test",
        cpu=CPUInfo(name="x", physical_cores=1, logical_cores=1, max_frequency_mhz=1000),
        ram=RAMInfo(total_gb=128, available_gb=100),
        gpus=[GPUInfo(name="RTX 4090", vram_mb=24576, vendor="NVIDIA")],
        storage=StorageInfo(total_gb=1000, used_gb=200, free_gb=800),
    )
    mc = classify_machine(hw)
    assert mc.tier == "Enthusiast"
    assert "Dedicated" in mc.rationale

def test_apple_silicon_unified_memory():
    hw = HardwareReport(
        os="Darwin",
        cpu=CPUInfo(name="Apple M2", physical_cores=8, logical_cores=8, max_frequency_mhz=3500),
        ram=RAMInfo(total_gb=32.0, available_gb=24.0),
        gpus=[GPUInfo(name="Apple M2", vram_mb=32768, vendor="Apple", is_unified_memory=True)],
        storage=StorageInfo(total_gb=512, used_gb=200, free_gb=312),
    )
    mc = classify_machine(hw)
    # With 32GB unified memory, should be High-End tier
    assert mc.tier == "High-End"
    assert "Unified" in mc.rationale

def test_intel_igpu_unified_memory():
    hw = HardwareReport(
        os="Windows",
        cpu=CPUInfo(name="Intel i7-12700H", physical_cores=12, logical_cores=20, max_frequency_mhz=4700),
        ram=RAMInfo(total_gb=16.0, available_gb=12.0),
        gpus=[GPUInfo(name="Intel UHD Graphics", vram_mb=0, vendor="Intel", is_unified_memory=True)],
        storage=StorageInfo(total_gb=512, used_gb=300, free_gb=212),
    )
    mc = classify_machine(hw)
    # With 16GB unified memory, should be Midrange tier
    assert mc.tier == "Midrange"
    assert "Unified" in mc.rationale

def test_amd_gpu():
    hw = HardwareReport(
        os="Linux",
        cpu=CPUInfo(name="AMD Ryzen 7", physical_cores=8, logical_cores=16, max_frequency_mhz=4200),
        ram=RAMInfo(total_gb=32.0, available_gb=24.0),
        gpus=[GPUInfo(name="AMD Radeon RX 6700 XT", vram_mb=12288, vendor="AMD")],
        storage=StorageInfo(total_gb=1000, used_gb=500, free_gb=500),
    )
    mc = classify_machine(hw)
    assert mc.tier == "High-End"
    assert "Dedicated" in mc.rationale