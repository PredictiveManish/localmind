"""Machine classification and model size recommendations."""
from .models import HardwareReport, MachineClass
from .constants import TIER_THRESHOLDS, TIER_THRESHOLDS_UNIFIED, TIER_PARAM_RANGES


def classify_machine(hw: HardwareReport) -> MachineClass:
    """
    Classify the machine into a tier based on RAM and VRAM.
    
    For Apple Silicon and Intel iGPUs with unified memory, uses more lenient
    thresholds since the GPU can access all system RAM.
    
    TIER_THRESHOLDS are defined in constants.py.
    """
    ram_gb = hw.ram.total_gb
    vram_gb = 0
    has_unified_memory = False
    
    if hw.gpus:
        # Check if any GPU uses unified memory
        for gpu in hw.gpus:
            if gpu.is_unified_memory:
                has_unified_memory = True
                # For unified memory, GPU can access all system RAM
                vram_gb = ram_gb
            else:
                vram_gb += gpu.vram_mb / 1024.0

    tier = "Tiny"
    rationale = ""
    
    # Use unified memory thresholds for Apple Silicon / Intel iGPUs
    thresholds = TIER_THRESHOLDS_UNIFIED if has_unified_memory else TIER_THRESHOLDS
    
    # Determine tier (prefer highest if multiple conditions match)
    for t_name, t_req in sorted(thresholds.items(), key=lambda x: x[1]["min_ram"], reverse=True):
        if ram_gb >= t_req["min_ram"] and vram_gb >= t_req.get("min_vram", 0):
            tier = t_name
            memory_type = "Unified" if has_unified_memory else "Dedicated"
            rationale = f"RAM: {ram_gb} GB, {memory_type} VRAM: {round(vram_gb, 1)} GB"
            break

    param_range = TIER_PARAM_RANGES.get(tier, "1B-4B")
    return MachineClass(
        tier=tier,
        rationale=rationale,
        recommended_param_range=param_range,
    )
