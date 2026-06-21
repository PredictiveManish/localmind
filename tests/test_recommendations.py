"""Tests for recommendation functions."""
from localmind.recommendations import general_recommendation, task_recommendations
from localmind.models import HardwareReport, CPUInfo, RAMInfo, StorageInfo

_SAMPLE_HW = HardwareReport(
    os="Linux",
    cpu=CPUInfo(name="i7", physical_cores=4, logical_cores=8, max_frequency_mhz=3000),
    ram=RAMInfo(total_gb=32, available_gb=20),
    gpus=[],
    storage=StorageInfo(total_gb=500, used_gb=100, free_gb=400),
)

def test_general_recommendation():
    mc = general_recommendation(_SAMPLE_HW)
    assert mc.tier in ("Tiny", "Entry", "Midrange", "High-End", "Enthusiast")
    assert "B" in mc.recommended_param_range

def test_task_recommendation_coding():
    recs = task_recommendations(_SAMPLE_HW, "coding")
    assert len(recs) > 0
    assert all(r.parameter_size for r in recs)

def test_task_invalid():
    recs = task_recommendations(_SAMPLE_HW, "invalid")
    assert len(recs) == 1
    assert recs[0].name == "No model found"