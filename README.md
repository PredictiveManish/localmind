# LocalMind

**LocalMind tells you which AI models will actually run on your machine — without the guesswork.**

You've been there: you see a cool model on Ollama's library, download it, and then… your laptop chugs like it's pulling a truck. LocalMind fixes this. It scans your hardware, figures out what you're working with, and tells you exactly which models will run smoothly — and which ones will make your fan sound like a jet engine.

```bash
pip install localmind
lm doctor
```

That's it. One command. You get your hardware tier, warnings about bottlenecks, and model recommendations tailored to your actual machine. Not someone else's.

---

## What can it do?

All commands work with `lm` (short) or `localmind` (long). Pick your poison.

| Command | What happens |
|---|---|
| `lm hardware` | Shows your CPU, RAM, GPU (with VRAM), and disk space |
| `lm recommend` | Tells you your machine's tier and what model sizes fit |
| `lm recommend coding` | Suggests models good at code generation for your hardware |
| `lm recommend writing` | Suggests models good at writing/content for your hardware |
| `lm recommend reasoning` | Suggests models good at logic/analysis for your hardware |
| `lm doctor` | Full diagnostic — hardware, tier, warnings, recommendations |
| `lm search llama` | Searches the Ollama library for models matching your query |
| `lm info llama3:8b` | Shows metadata for a model you've already downloaded |
| `lm download llama3:8b` | Pulls a model (auto-installs Ollama if you don't have it) |
| `lm help` | Prints everything above with explanations and examples |

---

## How does it actually work?

Here's the thing — running a local LLM isn't just about having a GPU. It's about the **relationship** between your RAM, your VRAM, and the model's parameter size. LocalMind figures out that relationship for you.

### Step 1: Hardware scan

LocalMind looks at your system using `psutil` (for CPU, RAM, disk) and multi-vendor GPU detection:

- **NVIDIA GPUs** → GPUtil reads VRAM directly
- **AMD GPUs** → WMI on Windows, sysfs/rocm-smi on Linux
- **Intel integrated graphics** → WMI on Windows, sysfs on Linux (these share system RAM, so they're handled differently)
- **Apple Silicon** → `system_profiler` on macOS (M1/M2/M3 — these use unified memory, which changes the math entirely)

It doesn't just say "you have a GPU." It tells you **what kind** of GPU, **how much VRAM** it has, and whether that VRAM is dedicated or shared with the CPU.

### Step 2: Tier classification

Your machine gets slotted into one of five tiers based on RAM and VRAM:

| Tier | What it means | Example machines |
|---|---|---|
| **Tiny** | Barely anything | Raspberry Pi, old laptops, 4GB RAM machines |
| **Entry** | Can handle small models | 8GB RAM laptop, integrated graphics |
| **Midrange** | The sweet spot for most people | 16GB RAM + GTX 1650, MacBook Air M2 16GB |
| **High-End** | Serious local AI territory | 32GB RAM + RTX 3060, MacBook Pro M2 32GB |
| **Enthusiast** | Run the big stuff | 64GB+ RAM + RTX 4090, Mac Studio M2 Ultra |

**Here's the key insight:** A MacBook with 32GB unified memory gets classified differently than a Windows PC with 32GB RAM and no GPU. On Apple Silicon, the GPU can access all system RAM as VRAM. On Windows without a dedicated GPU, that RAM is useless for AI inference. LocalMind knows this difference.

### Step 3: Model recommendations

Once it knows your tier, it suggests models. Two modes:

- **General** — "Try models in the 7B–14B parameter range"
- **Task-specific** — "For coding, try `codellama:13b` or `deepseek-coder:6.7b`"

The model lists are curated in `constants.py`. They're not randomly generated — they're based on what the community has found works well for each task.

### Step 4: Ollama integration

LocalMind doesn't just tell you what to run — it helps you get there:

- `lm search <query>` queries the Ollama library API and shows you matching models sorted by popularity
- `lm download <model>` runs `ollama pull` and streams progress to your terminal. If you don't have Ollama installed? It downloads and installs it for you (Windows PowerShell, macOS/Linux shell scripts)
- `lm info <model>` shows metadata for locally pulled models (architecture, parameters, quantization info)

---

## What's under the hood?

```
localmind/
├── cli.py               # All the commands (Typer framework)
├── hardware.py           # System scanning — CPU, RAM, GPU, disk
├── classifier.py         # RAM + VRAM → tier mapping (handles unified memory)
├── recommendations.py    # General + task-specific model suggestions
├── doctor.py             # Aggregates everything into a diagnostic report
├── ollama_api.py         # Ollama library search + local CLI calls + auto-install
├── models.py             # Pydantic data structures (type-safe, validated)
├── constants.py          # Tier thresholds, model recommendation tables
└── utils.py              # Warnings, logging helpers
```

Everything is structured so you can change the tier thresholds or swap out model recommendations by editing `constants.py`. No config files, no environment variables, no hidden magic.

---

## Why does this exist?

Because choosing a local AI model shouldn't require reading benchmark tables, calculating VRAM requirements, or guessing quantization levels. You should be able to run one command and know:

1. What hardware you have (and whether it's a bottleneck)
2. What tier your machine is in
3. Which models will actually run without melting your laptop
4. Which models are best for what you want to do (code, writing, reasoning)

LocalMind does all four.

---

## Quick examples

```bash
# See everything about your machine
lm hardware

# Get a full diagnostic with recommendations
lm doctor

# See what fits your machine
lm recommend

# Find models good at coding
lm recommend coding

# Search the Ollama library
lm search "coding assistant"

# Download a model (Ollama gets installed automatically if needed)
lm download codellama:13b

# Check metadata on a model you already pulled
lm info codellama:13b
```

---

## Hardware tier thresholds

The thresholds live in `localmind/constants.py`. Here's what they look like:

| Tier | Min RAM | Min VRAM | Recommended model size |
|---|---|---|---|
| Enthusiast | 64 GB | 16 GB | 32B–70B+ |
| High-End | 32 GB | 8 GB | 14B–32B |
| Midrange | 16 GB | 4 GB | 7B–14B |
| Entry | 8 GB | 2 GB | 4B–8B |
| Tiny | any | any | 1B–4B |

For **Apple Silicon** and **Intel integrated GPUs** with unified memory, the thresholds are more lenient because the GPU can access all system RAM. A MacBook Pro M2 with 32GB unified memory is classified as **High-End**, while a Windows PC with 32GB RAM but no GPU would be **Entry**.

Want to change the thresholds? Edit `TIER_THRESHOLDS` in `constants.py`. Want to add a new tier? Just add an entry. It's that simple.

---

## Requirements

- **Python 3.11 or later**
- **Ollama** — only needed for `lm download` and `lm info`. If you run `lm download` without it, LocalMind installs it automatically
- **A GPU is optional** — CPU inference works, it's just slower. A dedicated GPU (NVIDIA/AMD) or Apple Silicon gives you the best experience

---

## Development

```bash
git clone https://github.com/predictivemanish/localmind.git
cd localmind
pip install -e ".[dev]"
pytest
```

---

## License

MIT
