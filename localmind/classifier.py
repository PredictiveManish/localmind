"""Machine classification and model size recommendations."""
from .models import HardwareReport, MachineClass
from .constants import TIER_THRESHOLDS, TIER_PARAM_RANGES


def classify_machine(hw: HardwareReport) -> MachineClass:
    """
    Classify the machine into a tier based on RAM and VRAM.
    TIER_THRESHOLDS are defined in constants.py.
    """
    ram_gb = hw.ram.total_gb
    vram_gb = 0
    if hw.gpus:
        vram_gb = sum(g.vram_mb for g in hw.gpus) / 1024.0

    tier = "Tiny"
    rationale = ""
    
    # Determine tier (prefer highest if multiple conditions match)
    for t_name, t_req in sorted(TIER_THRESHOLDS.items(), key=lambda x: x[1]["min_ram"], reverse=True):
        if ram_gb >= t_req["min_ram"] and vram_gb >= t_req.get("min_vram", 0):
            tier = t_name
            rationale = f"RAM: {ram_gb} GB, VRAM: {round(vram_gb, 1)} GB"
            break

    param_range = TIER_PARAM_RANGES.get(tier, "1B-4B")
    return MachineClass(
        tier=tier,
        rationale=rationale,
        recommended_param_range=param_range,
    )