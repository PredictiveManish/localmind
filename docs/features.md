# Features & Architecture

This page explains how LocalMind actually works under the hood. Not the marketing version — the real version.

## Hardware Detection

LocalMind scans your system using `psutil` for CPU, RAM, and disk. But GPU detection is where things get interesting.

### Why GPU Detection Is Hard

There is **no cross-platform GPU API**. Every platform, every vendor, uses different tools:

| Platform | NVIDIA | AMD | Intel | Apple |
|---|---|---|---|---|
| **Windows** | GPUtil | WMI (`Win32_VideoController`) | WMI (`Win32_VideoController`) | N/A |
| **macOS** | N/A | N/A | N/A | `system_profiler` |
| **Linux** | GPUtil | sysfs + rocm-smi | sysfs | N/A |

So LocalMind has **8 separate detection functions**, one for each platform/vendor combination. The orchestrator (`get_gpu_info`) checks the platform first, then tries each detector. If a detector fails (e.g., GPImportError, WMI not available), it's silently skipped.

### NVIDIA Detection

Uses the `GPUtil` library, which wraps the NVIDIA Management Library (NVML). This is the most reliable method because NVML is the official NVIDIA API:

```python
import GPUtil
gpus = GPUtil.getGPUs()
for gpu in gpus:
    print(gpu.name, gpu.memoryTotal, gpu.driver)
```

GPUtil is only installed on non-macOS systems (NVIDIA doesn't ship in Macs). On macOS, this dependency is skipped entirely.

### AMD Detection

Two methods, depending on the platform:

**Windows**: Uses WMI (Windows Management Instrumentation):
```python
import win32com.client
wmi = win32com.client.Dispatch("WbemScripting.SWbemLocator")
service = wmi.ConnectServer(".")
gpus = service.ExecQuery("SELECT * FROM Win32_VideoController")
```
Filters results for GPUs with "AMD", "Radeon", or "RX" in the name.

**Linux**: Uses sysfs (`/sys/bus/pci/devices/`):
- Reads `/sys/bus/pci/devices/{device}/vendor` to check if vendor ID is `0x1002` (AMD)
- Checks `/sys/bus/pci/devices/{device}/class` to confirm it's a display controller (`030000`)
- Reads `/sys/bus/pci/devices/{device}/device/driver/device/name` for the GPU name
- Reads `/sys/bus/pci/devices/{device}/resource` to extract VRAM

If sysfs doesn't return results, falls back to `rocm-smi --showallinfo` (AMD's ROCm monitoring tool).

### Intel Integrated GPU Detection

**Windows**: Same WMI approach as AMD, but filters for "Intel", "UHD", or "Iris" in the name.

**Linux**: Same sysfs approach as AMD, but checks for vendor ID `0x8086` (Intel).

**Key difference**: Intel GPUs are marked with `is_unified_memory=True` because integrated GPUs share system RAM with the CPU. They don't have dedicated VRAM.

### Apple Silicon Detection

macOS doesn't have NVIDIA, AMD, or Intel GPUs in modern Macs. Instead, it uses Apple Silicon (M1/M2/M3) with a unified memory architecture.

Detection uses `system_profiler SPDisplaysDataType`, which is macOS's built-in hardware profiling tool:

```bash
system_profiler SPDisplaysDataType
```

This outputs information like:
```
Chipset Model: Apple M2
Total Number of Displays: 1
Display Type: Displays
Bus: Built-in
Total Bits per Pixel: 32
Total Displays: 1
Memory: 16 GB unified memory
```

**The VRAM estimation problem**: Apple doesn't expose GPU memory separately — it's unified with system RAM. So LocalMind maps total RAM to known GPU memory configurations based on Apple's official specs:

| Total RAM | Estimated GPU Memory | Mac Models |
|---|---|---|
| 8 GB | 16 GB | M1/M2/M3 base |
| 16 GB | 32 GB | M1/M2/M3 |
| 24 GB | 64 GB | M2/M3 |
| 36 GB | 96 GB | M2/M3 Pro/Max |
| 64 GB | 128 GB | M2/M3 Max |
| 128 GB | 192 GB | M3 Ultra |

This is a lookup table, not a calculation, because the actual GPU memory split is determined by the silicon, not by available RAM.

## Tier Classification

Once hardware is scanned, the classifier maps your specs to one of five tiers:

| Tier | Min RAM | Min VRAM | What it means |
|---|---|---|---|
| **Tiny** | any | any | Raspberry Pi, old laptops, 4GB RAM machines |
| **Entry** | 8 GB | 2 GB | Basic machines with integrated graphics |
| **Midrange** | 16 GB | 4 GB | The sweet spot — 16GB RAM + entry GPU |
| **High-End** | 32 GB | 8 GB | Serious local AI — 32GB RAM + decent GPU |
| **Enthusiast** | 64 GB | 16 GB | Top-tier — run the big models |

### The Classification Algorithm

```python
def classify_machine(hw):
    ram_gb = hw.ram.total_gb
    vram_gb = 0
    has_unified_memory = False
    
    for gpu in hw.gpus:
        if gpu.is_unified_memory:
            has_unified_memory = True
            vram_gb = ram_gb  # GPU can access ALL system RAM
        else:
            vram_gb += gpu.vram_mb / 1024.0
    
    # Choose thresholds based on memory type
    thresholds = TIER_THRESHOLDS_UNIFIED if has_unified_memory else TIER_THRESHOLDS
    
    # Check from highest to lowest tier
    for tier, req in sorted(thresholds, key=lambda x: x[1]["min_ram"], reverse=True):
        if ram_gb >= req["min_ram"] and vram_gb >= req.get("min_vram", 0):
            return tier
```

**Why iterate from highest to lowest?** Because we want the best matching tier. A machine with 64GB RAM and 24GB VRAM matches both "High-End" (32GB RAM, 8GB VRAM) and "Enthusiast" (64GB RAM, 16GB VRAM). We want "Enthusiast", so we check from the top and break on the first match.

### Unified Memory vs Dedicated VRAM

This is the most important concept in LocalMind:

**Dedicated VRAM** (NVIDIA, AMD): The GPU has its own memory. If a 7B model at Q4 quantization needs ~5GB VRAM, and your GPU has 6GB, it fits. If your GPU has 4GB, it doesn't fit — and there's nothing you can do about it.

**Unified Memory** (Apple Silicon, Intel iGPU): The GPU and CPU share the same memory pool. A MacBook with 32GB RAM means the GPU can potentially use all 32GB (minus what the OS needs). So a 7B model at Q4 that needs ~5GB can run even though there's no "dedicated VRAM."

This is why a MacBook Pro M2 with 32GB unified memory is classified as **High-End**, while a Windows PC with 32GB RAM and no GPU is classified as **Entry**. Same RAM, very different AI capabilities.

### Threshold Design Choices

The thresholds aren't arbitrary. They're based on practical model sizing:

- **2GB VRAM** → Can run 4B models at Q4 quantization (~3GB total)
- **4GB VRAM** → Can run 7B models at Q4 quantization (~5GB total)
- **8GB VRAM** → Can run 13B models at Q4 quantization (~8GB total)
- **16GB VRAM** → Can run 34B models at Q4 quantization (~20GB total)
- **24GB VRAM** → Can run 70B models at Q4 quantization (~40GB total, with system RAM overflow)

The RAM thresholds complement the VRAM thresholds because:
- CPU inference needs system RAM (the model loads into RAM, not VRAM)
- If a model doesn't fit in VRAM, it spills into system RAM (slower but still works)
- The OS needs RAM too (2-4GB minimum)

## Recommendation Engine

### General Recommendations

`lm recommend` returns the tier's parameter size range. For a Midrange machine: "7B-14B". This tells you what size models to target without prescribing a specific model.

### Task-Specific Recommendations

`lm recommend coding` looks up the tier in `TASK_RECOMMENDATIONS` and returns model names:

```python
TASK_RECOMMENDATIONS = {
    "coding": {
        "Midrange": ["codellama:13b", "deepseek-coder:6.7b"],
        "High-End": ["deepseek-coder:33b", "codellama:34b"],
    },
    "writing": {
        "Midrange": ["mistral:7b", "llama3:8b"],
        "High-End": ["llama3:70b", "command-r:35b"],
    },
    "reasoning": {
        "Midrange": ["llama3:8b", "mixtral:8x7b"],
        "High-End": ["llama3:70b", "qwen:72b"],
    },
}
```

**Why these models?** Because they're known to excel at their respective tasks:
- `codellama` and `deepseek-coder` were trained specifically on code corpora
- `llama3` and `mistral` are strong general-purpose models good at writing
- `qwen:72b` and `llama3:70b` excel at reasoning due to their training data

**Why hardcoded?** Because the Ollama library has hundreds of models. Hardcoding the "best" ones per tier per task is simpler than building a recommendation engine. Future versions could source this from benchmark data (Hugging Face LMSYS leaderboard, LMSYS Chatbot Arena).

### Parameter Size Extraction

When displaying recommendations, LocalMind extracts the parameter size from the model name:

```python
for part in name.split(":"):
    if "b" in part.lower():
        param_size = part.upper()
        break
```

For `codellama:13b`, this splits on `:`, finds the part containing "b", and extracts "13B". It's a simple heuristic that works for Ollama's naming convention (`{model}:{size}b`).

## Ollama Integration

### Search

`lm search <query>` queries the Ollama library API:

```
GET https://ollama.com/api/library?q={query}&sort=popular
```

The API returns a dict where keys are model names and values are model objects:

```json
{
  "models": {
    "llama3": {
      "name": "llama3",
      "description": "Meta Llama 3...",
      "pulls": 1234567,
      "tags": ["8b", "70b"],
      "model_size": "4.7GB"
    }
  }
}
```

The code handles both dict and list formats defensively, in case the API schema changes.

### Inspect

`lm info <model>` runs `ollama show <model>` as a subprocess and parses the JSON output. This requires Ollama installed and the model already pulled.

### Download

`lm download <model>` runs `ollama pull <model>` and streams output line-by-line using `subprocess.Popen`. Before pulling, it checks if Ollama is installed and auto-installs it if missing.

**Auto-install flow:**

```
User runs: lm download llama3
                    │
                    ▼
        ┌─────────────────────┐
        │ Is Ollama installed?│
        └────────┬────────────┘
                 │
        ┌────────┴────────┐
        │                 │
       Yes               No
        │                 │
        ▼                 ▼
   ollama pull     Download official installer
   llama3          (PowerShell / shell script)
                    │
                    ▼
            ollama pull llama3
```

**Platform-specific installers:**
- **Windows**: `powershell -ExecutionPolicy Bypass -Command "irm https://ollama.com/install.ps1 | iex"`
- **macOS/Linux**: `curl -fsSL https://ollama.com/install.sh | sh`

These are Ollama's official installation methods. LocalMind doesn't bundle installers — it downloads and runs them directly.

## Architecture Overview

```
                    User runs: lm doctor
                              │
                              ▼
              ┌───────────────────────────────┐
              │         cli.py (Typer)        │  ← Thin presenter, no logic
              │  Just formats and displays    │
              └───────────────┬───────────────┘
                              │
              ┌───────────────┴───────────────┐
              │    doctor.py (orchestrator)   │  ← Assembles everything
              └──┬──────┬──────┬──────┬───────┘
                 │      │      │      │
          ┌──────┐ ┌────┐ ┌────┐ ┌────────┐
          │hw.py │ │cls │ │warn│ │  recs   │
          └──┬───┘ └──┬─┘ └──┬─┘ └────┬───┘
             │         │        │         │
             ▼         ▼        ▼         ▼
         Hardware   Tier    Warnings  Models
         Report     Class              Recommend
```

**Data flow:**
1. `hardware.py` scans → `HardwareReport`
2. `classifier.py` consumes `HardwareReport` → `MachineClass`
3. `utils.py` consumes `HardwareReport` → `List[str]` warnings
4. `recommendations.py` consumes both → `List[ModelRecommendation]`
5. `doctor.py` assembles everything → `DoctorReport`
6. `cli.py` consumes `DoctorReport` → prints to terminal

**Design principles:**
- **Pipeline architecture** — each stage takes structured input, transforms it, passes it forward
- **No side effects** — functions don't print, don't modify global state
- **Validation at boundaries** — Pydantic models guarantee data shape at every stage
- **Thin CLI layer** — `cli.py` only formats and displays, all logic is in other modules

## Extensibility

Everything customizable lives in `constants.py`:

```python
# Adjust tier thresholds
TIER_THRESHOLDS["Ultra"] = {"min_ram": 128, "min_vram": 32}
TIER_PARAM_RANGES["Ultra"] = "70B-120B"

# Add a new task
TASK_RECOMMENDATIONS["image"] = {
    "Midrange": ["llava:13b"],
    "High-End": ["llava:72b"],
}
```

No config files, no environment variables, no hidden magic. Edit `constants.py`, reinstall, done.

## Known Limitations

1. **Hardcoded model lists** — `TASK_RECOMMENDATIONS` becomes stale as new models ship. Not sourced from benchmarks.
2. **CPU-only inference speed** — The classifier doesn't account for CPU generation. A modern i3 beats an old i7, but both get the same tier if RAM/VRAM match.
3. **Multi-GPU setups** — VRAM is summed across GPUs, but Ollama may not utilize all GPUs simultaneously on all platforms.
4. **Intel iGPU VRAM** — On Linux, Intel integrated GPUs report 0 VRAM because they share system memory. The classifier handles this via `is_unified_memory`, but the `hardware` command shows "0 MB" which can be confusing.
5. **No disk speed detection** — NVMe vs HDD affects model loading time but isn't measured.
6. **No swap/RAM overflow warning** — If system RAM is nearly full, the classifier doesn't account for swap usage.
