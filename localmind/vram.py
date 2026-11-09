"""VRAM estimation engine.

Calculates how much VRAM and system RAM a model needs at each quantization
level. This is the most practical information for someone choosing which
model to download.

The math:
  - FP16 (half precision): 2 bytes per parameter
  - Q8_0 (8-bit quant):    ~1.08 bytes per parameter
  - Q5_K_M (5-bit quant):  ~0.7 bytes per parameter
  - Q4_0 (4-bit quant):    ~0.55 bytes per parameter
  - Q3_K_M (3-bit quant):  ~0.42 bytes per parameter

Example: llama3:8B at Q4_0
  8 billion params × 0.55 bytes = ~4.4 GB
  Plus overhead for KV cache, context window, etc. = ~5.2 GB total VRAM
"""
from __future__ import annotations
from typing import Dict, Optional
from .models import VRAMEstimate

# Quantization multipliers (bytes per parameter)
# Based on: https://github.com/ggerganov/ggml/blob/master/docs/quantization.md
QUANT_MULTIPLIERS: Dict[str, float] = {
    "FP16":    2.0,    # 16-bit floating point (largest, most accurate)
    "FP8":     1.0,    # 8-bit floating point
    "Q8_0":    1.08,   # 8-bit quantized (high quality)
    "Q6_K":    0.82,   # 6-bit quantized (very good)
    "Q5_K_M":  0.70,   # 5-bit quantized (good balance)
    "Q5_0":    0.68,   # 5-bit quantized
    "Q4_K_M":  0.58,   # 4-bit quantized (recommended default)
    "Q4_0":    0.55,   # 4-bit quantized (original)
    "Q3_K_M":  0.42,   # 3-bit quantized (smaller, less accurate)
    "Q3_K_L":  0.46,   # 3-bit quantized (larger variant)
    "Q2_K":    0.35,   # 2-bit quantized (smallest, lowest quality)
}

# Context window overhead estimates (in GB)
# Depends on model architecture and max context length
CONTEXT_OVERHEAD: Dict[str, float] = {
    "llama":    0.8,   # Llama-family models
    "mistral":  0.7,   # Mistral-family models
    "mixtral":  0.9,   # Mixtral (MoE, slightly more overhead)
    "gemma":    0.6,   # Gemma-family models
    "phi":      0.5,   # Phi-family models
    "qwen":     0.7,   # Qwen-family models
    "command-r":0.8,   # Command-R
    "default":  0.7,   # Fallback for unknown families
}

# Typical max context lengths per family (in tokens)
CONTEXT_LENGTHS: Dict[str, int] = {
    "llama":    8192,
    "mistral":  8192,
    "mixtral":  32768,
    "gemma":    8192,
    "phi":      16384,
    "qwen":     32768,
    "command-r":131072,
    "default":  8192,
}


def estimate_vram(model_name: str, quantization: Optional[str] = None,
                  available_vram_gb: float = 0.0, available_ram_gb: float = 0.0,
                  max_context: int = 8192) -> list[VRAMEstimate]:
    """
    Estimate VRAM and RAM requirements for a model at all quantization levels.

    Parameters:
        model_name: e.g. "llama3:8b", "codellama:34b"
        quantization: specific quant to estimate (if None, estimates all)
        available_vram_gb: GPU VRAM available (for fits_in_vram check)
        available_ram_gb: System RAM available (for fits_in_ram check)
        max_context: context window size in tokens (default 8192)

    Returns:
        List of VRAMEstimate objects, one per quantization level,
        sorted by size (smallest first).
    """
    # Extract parameter count from model name (e.g., "llama3:8b" → 8.0)
    params_b = _extract_params(model_name)
    if params_b <= 0:
        # Without a parameter count every number below would be invented; an
        # empty result is more honest than a plausible-looking 0.7 GB.
        return []

    # Detect model family from name
    family = _detect_family(model_name)

    results = []
    quantizations = [quantization] if quantization else list(QUANT_MULTIPLIERS.keys())

    for quant in quantizations:
        if quant not in QUANT_MULTIPLIERS:
            continue

        multiplier = QUANT_MULTIPLIERS[quant]
        # Base model size (weights only).
        # params_b is in billions and multiplier is bytes per parameter, so the
        # product is already in GB: 8e9 params x 0.55 bytes = 4.4e9 bytes = 4.4 GB.
        weight_gb = params_b * multiplier

        # Context/KV cache overhead scales with context length and layers
        # Rough estimate: overhead ≈ base_overhead × (context / default_context)
        default_context = CONTEXT_LENGTHS.get(family, CONTEXT_LENGTHS["default"])
        context_factor = max_context / default_context
        overhead_gb = CONTEXT_OVERHEAD.get(family, CONTEXT_OVERHEAD["default"]) * (0.5 + 0.5 * context_factor)

        total_gb = weight_gb + overhead_gb

        # VRAM needed = total (if all layers offloaded to GPU)
        # RAM needed = total × 1.2 (some overhead for CPU inference)
        vram_gb = total_gb
        ram_gb = total_gb * 1.2

        results.append(VRAMEstimate(
            model_name=model_name,
            quantization=quant,
            size_gb=round(total_gb, 2),
            vram_gb=round(vram_gb, 2),
            ram_gb=round(ram_gb, 2),
            params_billion=round(params_b, 2),
            fits_in_vram=available_vram_gb > 0 and vram_gb <= available_vram_gb * 0.9,
            fits_in_ram=available_ram_gb > 0 and ram_gb <= available_ram_gb * 0.9,
        ))

    # Sort by size
    results.sort(key=lambda x: x.size_gb)
    return results


def get_best_quant(model_name: str, available_vram_gb: float,
                   available_ram_gb: float) -> Optional[VRAMEstimate]:
    """
    Find the largest model quantization that fits in available hardware.

    Tries from highest quality to lowest, returns the first one that fits.

    Parameters:
        model_name: e.g. "llama3:8b"
        available_vram_gb: GPU VRAM (0 = CPU only)
        available_ram_gb: System RAM

    Returns:
        VRAMEstimate for the best fitting quantization, or None if nothing fits.
    """
    estimates = estimate_vram(model_name, available_vram_gb=available_vram_gb,
                              available_ram_gb=available_ram_gb)

    if not estimates:
        return None

    # If we have VRAM, prefer highest quality that fits in VRAM
    if available_vram_gb > 0:
        for est in reversed(estimates):
            if est.fits_in_vram:
                return est

    # Fall back to RAM-based fitting
    for est in reversed(estimates):
        if est.fits_in_ram:
            return est

    # Nothing fits - return None
    return None


def format_vram_table(estimates: list[VRAMEstimate], available_vram_gb: float = 0.0,
                      available_ram_gb: float = 0.0) -> str:
    """
    Format VRAM estimates as a readable string table.

    Parameters:
        estimates: list of VRAMEstimate from estimate_vram()
        available_vram_gb: user's GPU VRAM (for indicator)
        available_ram_gb: user's system RAM (for indicator)

    Returns:
        Formatted table string suitable for printing or display.
    """
    lines = []
    lines.append(f"{'Quant':<10} {'Size':>8} {'VRAM':>8} {'RAM':>8}  {'Fits'}")
    lines.append("-" * 55)

    for est in estimates:
        # Indicator column
        if available_vram_gb > 0:
            if est.fits_in_vram:
                indicator = "[green]✓ VRAM[/green]"
            else:
                indicator = f"[red]✗ VRAM[/red] (need {est.vram_gb:.1f}GB)"
        elif available_ram_gb > 0:
            if est.fits_in_ram:
                indicator = "[yellow]✓ RAM[/yellow]"
            else:
                indicator = f"[red]✗ RAM[/red] (need {est.ram_gb:.1f}GB)"
        else:
            indicator = "?"

        lines.append(
            f"{est.quantization:<10} {est.size_gb:>6.1f}GB {est.vram_gb:>6.1f}GB {est.ram_gb:>6.1f}GB  {indicator}"
        )

    return "\n".join(lines)


# ────────────────────── internal helpers ──────────────────────

def _extract_params(model_name: str) -> float:
    """Extract parameter count in billions from model name.

    Examples:
        "llama3:8b" → 8.0
        "codellama:34b" → 34.0
        "mixtral:8x7b" → 46.7 (total: 8 × 7)
        "phi3:mini" → 3.8 (approximate)
        "gemma:2b" → 2.0
    """
    import re

    # Known model mappings for names without explicit param count
    known_params = {
        "phi3:mini": 3.8,
        "phi3:medium": 14.0,
        "stablelm-zephyr:3b": 3.0,
        "tinyllama": 1.1,
        "llama3": 8.0,
        "llama3:70b": 70.0,
        "llama3:405b": 405.0,
        "mistral": 7.0,
        "mistral:7b": 7.0,
        "mistral:8x7b": 56.0,
        "mistral:8x22b": 141.0,
        "mixtral:8x7b": 46.7,
        "codellama": 7.0,
        "codellama:13b": 13.0,
        "codellama:34b": 34.0,
        "deepseek-coder": 6.7,
        "deepseek-coder:33b": 33.0,
        "qwen:0.5b": 0.5,
        "qwen:1.5b": 1.5,
        "qwen:4b": 4.0,
        "qwen:7b": 7.0,
        "qwen:14b": 14.0,
        "qwen:32b": 32.0,
        "qwen:72b": 72.0,
        "gemma:2b": 2.0,
        "gemma:7b": 7.0,
        "command-r": 35.0,
        "falcon": 7.0,
        "llava": 7.0,
    }

    # Known models first: a MoE tag cannot be multiplied out (mixtral:8x7b is
    # 46.7B total parameters, not 8 x 7 = 56B), so an explicit table wins.
    if model_name in known_params:
        return known_params[model_name]

    # Explicit size tag, e.g. "llama3:8b" or "qwen:0.5b"
    match = re.search(r':(\d+\.?\d*)b', model_name, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # MoE tag, e.g. "mixtral:8x7b" for models not in the table
    match = re.search(r':(\d+)x(\d+)b', model_name, re.IGNORECASE)
    if match:
        return float(match.group(1)) * float(match.group(2))

    # Try prefix match
    for name, params in known_params.items():
        if model_name.startswith(name.split(":")[0]):
            return params

    return 0.0  # Unknown


def _detect_family(model_name: str) -> str:
    """Detect model family from model name to estimate context overhead.

    Returns family name like 'llama', 'mistral', 'gemma', etc.
    """
    name = model_name.lower().split(":")[0]  # Remove tag

    family_map = {
        "llama": "llama",
        "llava": "llama",
        "mistral": "mistral",
        "mixtral": "mixtral",
        "gemma": "gemma",
        "gemma2": "gemma",
        "phi": "phi",
        "phi3": "phi",
        "qwen": "qwen",
        "qwen2": "qwen",
        "command-r": "command-r",
        "deepseek": "qwen",  # Similar architecture to Qwen
        "deepseek-coder": "qwen",
        "codellama": "llama",
        "stablelm": "llama",
        "falcon": "llama",
        "nemotron": "llama",
        "dolphin": "mistral",  # Fine-tuned on Mistral
        "neural-chat": "mistral",
        "solar": "llama",
        "yi": "llama",
    }

    for key, family in family_map.items():
        if key in name:
            return family

    return "default"
