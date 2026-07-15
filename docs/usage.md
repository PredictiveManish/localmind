# Usage Guide

All examples use the `lm` alias. The full `localmind` command works identically.

## lm hardware — See What You're Working With

This is your starting point. It scans every major component of your system and shows you what you have:

```bash
lm hardware
```

**What you'll see:**

```
┌─────────────────────────────────────────────────┐
│              Hardware Information               │
├──────────────┬──────────────────────────────────┤
│ OS           │ macOS Sonoma 14.5                │
│ CPU          │ Apple M2                         │
│ Physical cores│ 8                               │
│ Logical cores│ 8                                │
│ Max frequency│ 3500 MHz                         │
│ RAM total    │ 16.0 GB                          │
│ RAM available│ 11.2 GB                          │
│ GPU          │ Apple M2 (16384 MB VRAM) [Unified Memory] │
│ Disk total   │ 512.0 GB                         │
│ Disk used    │ 298.0 GB                         │
│ Disk free    │ 214.0 GB                         │
└──────────────┴──────────────────────────────────┘
```

**What to look for:**
- **GPU line** — Shows the vendor (Apple, NVIDIA, AMD, Intel) and whether it's unified memory
- **RAM available** — This is what matters, not total RAM. If available is much lower than total, you're memory-constrained
- **Disk free** — Each Ollama model is 2–10GB. Make sure you have room

**On different platforms:**

- **Windows with NVIDIA**: Shows GPU name, VRAM, and driver version
- **Windows with AMD**: Detects via WMI, shows GPU name and VRAM
- **Windows with Intel**: Detects integrated graphics, marks as "Unified Memory"
- **macOS**: Detects Apple Silicon via `system_profiler`, estimates GPU memory from Mac model
- **Linux with NVIDIA**: Uses GPUtil for accurate VRAM reading
- **Linux with AMD**: Uses sysfs or rocm-smi depending on what's available
- **Linux with Intel**: Detects integrated graphics via sysfs, marks as "Unified Memory"

## lm recommend — What Models Fit Your Machine?

This is the core feature. It scans your hardware, classifies your machine into a tier, and tells you what model sizes will run well:

```bash
lm recommend
```

**Example output:**

```
Machine tier: Midrange
Recommended parameter range: 7B-14B
RAM: 32.0 GB, Dedicated VRAM: 6.0 GB
```

**What this means:**
- **Midrange** — Your machine sits in the middle of the pack. Not the smallest, not the biggest.
- **7B-14B** — Models in this parameter range will run comfortably. Smaller models run faster. Larger models are smarter but slower.
- **Dedicated VRAM: 6.0 GB** — Your GPU has 6GB of its own memory. This is the hard limit for GPU inference.

**On Apple Silicon or Intel iGPU:**

```
Machine tier: High-End
Recommended parameter range: 14B-32B
RAM: 32.0 GB, Unified VRAM: 32.0 GB
```

Notice "Unified VRAM: 32.0 GB" — because the GPU can access all 32GB of system RAM, it gets classified as High-End instead of Entry.

### Task-Specific Recommendations

Want models optimized for a specific job? Add a task:

```bash
lm recommend coding      # Code generation, completion, debugging
lm recommend writing     # Creative writing, summarization, content
lm recommend reasoning   # Logic, analysis, problem-solving
```

**Example output (`lm recommend coding`):**

```
┌──────────────────────────────────────────────────┐
│      Recommendations for coding on your machine   │
├────────────────┬──────────────┬──────────────────┤
│ Model          │ Parameters   │ Notes            │
├────────────────┼──────────────┼──────────────────┤
│ codellama:13b  │ 13B          │ Good for coding  │
│ deepseek-coder │ 6.7B         │ Good for coding  │
└────────────────┴──────────────┴──────────────────┘
```

**Why different models for different tasks?**

Not all models are equally good at everything. `codellama` was trained specifically on code, so it's better at programming than general-purpose models. `llama3:70b` is great at reasoning because it was trained on diverse reasoning datasets. The model lists in `constants.py` are curated based on what the community has found works best.

**Available tasks:**

| Task | What it's good for |
|---|---|
| `coding` | Code generation, completion, debugging, refactoring |
| `writing` | Creative writing, summarization, email drafting, content |
| `reasoning` | Logic puzzles, mathematical reasoning, data analysis |

## lm doctor — The Full Picture

`lm doctor` combines everything into one comprehensive report:

```bash
lm doctor
```

**What it shows:**

1. **Hardware summary** — CPU, RAM, GPU, disk (same as `lm hardware` but as text)
2. **Classification** — Your tier and recommended model size
3. **Warnings** — Potential bottlenecks (low RAM, no GPU, low disk space)
4. **Recommendations** — General model suggestions based on your tier

**Example output:**

```
╭──────────────────────────────────────╮
│      🩺 LocalMind Doctor Report      │
├──────────────────────────────────────┤
│ Hardware                             │
│   OS: Ubuntu 22.04                   │
│   CPU: AMD Ryzen 7 5800X (8 cores)   │
│   RAM: 32.0 GB total, 24.0 GB avail  │
│   GPU: AMD Radeon RX 6700 XT (12288 MB) │
│   Storage: 450 GB free / 1000 GB     │
│                                      │
│ Classification                       │
│   Tier: High-End                     │
│   Recommended model size: 14B-32B    │
│                                      │
│ Warnings                             │
│   (none — your system looks good!)   │
│                                      │
│ Recommendations                      │
│   • General recommendation (14B-32B) │
│     Based on your hardware...        │
╰──────────────────────────────────────╯
```

**When to use it:**
- First time setting up — get a complete picture of your system
- Before downloading a model — make sure your system can handle it
- Troubleshooting — see if there are warnings about bottlenecks

## lm search — Find Models in the Ollama Library

Search for models by keyword:

```bash
lm search llama
lm search coding
lm search "reasoning model"
```

**Example output:**

```
Searching for models matching 'llama'...

┌──────────┬─────────────────────────┬───────────────┐
│ Name     │ Description             │ Popularity    │
├──────────┼─────────────────────────┼───────────────┤
│ llama3   │ Meta Llama 3 8B...      │ 1.2M pulls    │
│ llama2   │ Meta Llama 2 7B...      │ 850K pulls    │
│ llama3:8b│ Meta Llama 3 8B...      │ 980K pulls    │
│ llama3:70b│ Meta Llama 3 70B...    │ 340K pulls    │
└──────────┴─────────────────────────┴───────────────┘
```

**Tips:**
- Results are sorted by popularity (most pulls first)
- Try specific keywords: "coder", "mistral", "phi", "qwen"
- The search queries the Ollama library API at `ollama.com/api/library`

## lm info — Inspect a Downloaded Model

See metadata for a model you've already pulled:

```bash
lm info llama3:8b
```

**What you'll see:**
- Model architecture (e.g., LlamaForCausalLM)
- Number of parameters
- Quantization type (Q4_0, Q5_K_M, etc.)
- File sizes for each layer
- Tokenizer info
- System prompt and template

**Requirements:**
- Ollama must be installed
- The model must already be downloaded (`ollama pull llama3:8b`)

**Why use this?** To understand a model's resource requirements before running it. A 70B model needs significantly more VRAM than an 8B model.

## lm download — Pull a Model

Download a model from the Ollama library:

```bash
lm download llama3:8b
lm download codellama:13b
lm download mistral:7b
```

**What happens:**
1. LocalMind checks if Ollama is installed
2. If not, it automatically installs Ollama (one-time setup)
3. Runs `ollama pull <model>` and streams progress to your terminal

**Example output:**

```
Pulling model llama3:8b…
pulling manifest
pulling 6eeb80ea3609...   0% ▏                   0 B/4.2 GB
pulling 6eeb80ea3609...  25% ██▎               1.1 GB/4.2 GB
pulling 6eeb80ea3609...  50% ████▌             2.1 GB/4.2 GB
pulling 6eeb80ea3609...  75% ██████▎           3.2 GB/4.2 GB
pulling 6eeb80ea3609... 100% ██████████████████  4.2 GB/4.2 GB
```

**Tips:**
- Model names are case-sensitive: `llama3:8b` not `Llama3:8B`
- You can specify quantization: `llama3:70b-q4_0` for a quantized (smaller) version
- Larger models take longer to download and require more disk space

## lm help — Everything You Need to Know

```bash
lm help
```

Prints detailed documentation for every command, including:
- What each command does
- When to use it
- Examples
- Tips and best practices

## Workflow: The Recommended Order

New to LocalMind? Follow this order:

```bash
# 1. See what you have
lm hardware

# 2. Get a full diagnostic
lm doctor

# 3. See what fits your machine
lm recommend

# 4. Get task-specific suggestions
lm recommend coding

# 5. Search for a specific model
lm search "coding assistant"

# 6. Download the model
lm download codellama:13b

# 7. Inspect it
lm info codellama:13b
```

This is the natural flow: understand your hardware → see what fits → pick a model → download it.
