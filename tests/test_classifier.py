"""Tests for machine classification."""
from localmind.models import HardwareReport, CPUInfo, RAMInfo, StorageInfo
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
        gpus=[],  # No GPU – still limited to Tiny tier (VRAM requirement)
        storage=StorageInfo(total_gb=1000, used_gb=200, free_gb=800),  # ← Added
    )
    mc = classify_machine(hw)
    # Without a GPU, VRAM is 0, so even 128GB RAM doesn't bump it to Enthusiast.
    assert mc.tier == "Tiny"  # Because vram 0