"""Constants: tier definitions, model recommendations, parameter ranges."""

TIER_THRESHOLDS = {
    "Enthusiast": {"min_ram": 64, "min_vram": 16},
    "High-End":   {"min_ram": 32, "min_vram": 8},
    "Midrange":   {"min_ram": 16, "min_vram": 4},
    "Entry":      {"min_ram": 8,  "min_vram": 2},
    "Tiny":       {"min_ram": 0,  "min_vram": 0},  # fallback
}

# For Apple Silicon and Intel iGPUs with unified memory, VRAM = available system RAM
# These tiers are more lenient since the GPU can access all system memory
TIER_THRESHOLDS_UNIFIED = {
    "Enthusiast": {"min_ram": 48, "min_vram": 0},   # M2/M3 Max with 64-96GB RAM
    "High-End":   {"min_ram": 32, "min_vram": 0},   # M2/M3 Pro with 32GB RAM
    "Midrange":   {"min_ram": 16, "min_vram": 0},   # M1/M2/M3 base with 16GB RAM
    "Entry":      {"min_ram": 8,  "min_vram": 0},   # Base MacBook with 8GB RAM
    "Tiny":       {"min_ram": 0,  "min_vram": 0},   # fallback
}

TIER_PARAM_RANGES = {
    "Tiny":       "1B-4B",
    "Entry":      "4B-8B",
    "Midrange":   "7B-14B",
    "High-End":   "14B-32B",
    "Enthusiast": "32B-70B+",
}

# Static recommendation rules for specific tasks.
# Future: replace with benchmark-driven data.
TASK_RECOMMENDATIONS = {
    "coding": {
        "Tiny":       ["tinyllama:latest", "stablelm-zephyr:3b"],
        "Entry":      ["codellama:7b", "deepseek-coder:6.7b"],
        "Midrange":   ["codellama:13b", "deepseek-coder:6.7b"],
        "High-End":   ["deepseek-coder:33b", "codellama:34b"],
        "Enthusiast": ["deepseek-coder:33b", "codellama:34b"],
    },
    "writing": {
        "Tiny":       ["phi3:mini"],
        "Entry":      ["mistral:7b", "llama3:8b"],
        "Midrange":   ["mistral:7b", "llama3:8b"],
        "High-End":   ["llama3:70b", "command-r:35b"],
        "Enthusiast": ["llama3:70b", "mixtral:8x22b"],
    },
    "reasoning": {
        "Tiny":       ["phi3:mini"],
        "Entry":      ["llama3:8b", "gemma:7b"],
        "Midrange":   ["llama3:8b", "mixtral:8x7b"],
        "High-End":   ["llama3:70b", "qwen:72b"],
        "Enthusiast": ["llama3:70b", "qwen:72b"],
    },
}