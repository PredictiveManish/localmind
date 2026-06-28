# Features & Architecture

## Hardware Detection

LocalMind uses `psutil` for cross-platform system information and multi-vendor GPU detection for NVIDIA, AMD, Intel, and Apple Silicon.

| Component | Library | Details |
|---|---|---|
| **CPU** | `psutil` | Name, physical/logical cores, max frequency |
| **RAM** | `psutil` | Total and available memory in GB |
| **GPU** | GPUtil + WMI + sysfs + system_profiler | Name, VRAM, vendor (NVIDIA/AMD/Intel/Apple), unified memory detection |
| **Disk** | `psutil` | Total, used, and free space on root partition |
| **OS** | `platform` | System name and release version |

GPU detection works across all platforms:

- **NVIDIA**: GPUtil on Windows and Linux
- **AMD**: WMI on Windows, sysfs + rocm-smi on Linux
- **Intel**: WMI on Windows, sysfs on Linux (includes integrated GPUs with unified memory)
- **Apple Silicon**: `system_profiler` on macOS (detects M1/M2/M3 with unified memory)

Unified memory systems (Apple Silicon, Intel iGPUs) are classified using more lenient thresholds since the GPU can access all system RAM.

<!-- screenshot: lm hardware output -->

## Tier Classification

Once hardware is scanned, the classifier maps your specs to a performance tier. The thresholds are defined in `localmind/constants.py`:

| Tier | Min RAM | Min VRAM | Recommended Model Size |
|---|---|---|---|
| Enthusiast | 64 GB | 16 GB | 32B–70B+ |
| High-End | 32 GB | 8 GB | 14B–32B |
| Midrange | 16 GB | 4 GB | 7B–14B |
| Entry | 8 GB | 2 GB | 4B–8B |
| Tiny | — | — | 1B–4B |

For **Apple Silicon** and **Intel integrated GPUs** with unified memory, the classifier uses more lenient thresholds since the GPU can access all system RAM. A MacBook Pro M2 with 32GB unified memory is classified as High-End, while a Windows PC with 32GB RAM but no GPU would be classified as Entry.

The classifier iterates from highest to lowest tier and picks the first one where your hardware meets both RAM and VRAM thresholds. If both are met for multiple tiers, the higher tier wins.

```python
# Simplified classification logic
for tier, req in sorted(thresholds, key=descending_ram):
    if ram >= req["min_ram"] and vram >= req.get("min_vram", 0):
        return tier
```

## Recommendation Engine

### General Recommendations

The general recommendation (`lm recommend`) returns the tier's parameter size range — e.g., "7B-14B" for a Midrange machine. This tells you what size models to target without prescribing a specific model.

### Task-Specific Recommendations

For `coding`, `writing`, and `reasoning`, LocalMind maintains curated model lists per tier in `constants.py`:

```python
TASK_RECOMMENDATIONS = {
    "coding": {
        "Tiny":       ["tinyllama:latest", "stablelm-zephyr:3b"],
        "Entry":      ["codellama:7b", "deepseek-coder:6.7b"],
        "Midrange":   ["codellama:13b", "deepseek-coder:6.7b"],
        "High-End":   ["deepseek-coder:33b", "codellama:34b"],
        "Enthusiast": ["deepseek-coder:33b", "codellama:34b"],
    },
    # writing and reasoning follow the same pattern
}
```

These lists are currently **static** — curated based on community knowledge and model benchmarks. A future version may incorporate live benchmark data.

## Ollama Integration

### Search

The `search` command queries the [public Ollama API](https://ollama.com/api/library) (`api/library` endpoint) with your keyword and sorts results by popularity (pulls). This means you always see the most relevant models first.

### Inspect

`lm info` runs `ollama show <model>` locally and parses the JSON output. This requires Ollama installed and the model already pulled.

### Download

`lm download` calls `ollama pull <model>` and streams the download progress to your terminal in real time. Before pulling, it checks if Ollama is available:

```mermaid
flowchart LR
    A[lm download llama3] --> B{Ollama installed?}
    B -- Yes --> C[ollama pull llama3]
    B -- No --> D[Auto-install Ollama]
    D --> E[Download installer]
    E --> F[Run installer with progress bar]
    F --> C
```

### Automatic Installation

If Ollama is missing, LocalMind downloads and runs the official installer:

- **Windows**: `irm https://ollama.com/install.ps1 | iex`
- **macOS / Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

A Rich progress bar shows download progress during installation.

## Architecture Overview

```
localmind/
├── cli.py               # Typer CLI — all commands
├── hardware.py           # psutil + multi-vendor GPU detection (NVIDIA, AMD, Intel, Apple)
├── classifier.py         # RAM/VRAM → tier mapping (with unified memory support)
├── recommendations.py    # General + task-specific logic
├── doctor.py             # Aggregates everything into a report
├── ollama_api.py         # Search API, local ollama calls, auto-install
├── models.py             # Pydantic models (HardwareReport, MachineClass, etc.)
├── constants.py          # Tier thresholds, model tables
└── utils.py              # Logging, warning generation
```

<!-- screenshot: architecture diagram -->

## Extensibility

You don't need to fork the project to customise it. All tier thresholds and model recommendations live in a single file:

**`localmind/constants.py`**

- Change `TIER_THRESHOLDS` to adjust classification rules.
- Change `TIER_PARAM_RANGES` to tweak recommended parameter sizes.
- Change `TASK_RECOMMENDATIONS` to add, remove, or reorder models.

```python
# Example: add a new tier
TIER_THRESHOLDS["Ultra"] = {"min_ram": 128, "min_vram": 32}
TIER_PARAM_RANGES["Ultra"] = "70B-120B"
```

No configuration files, no environment variables, no hidden magic.
