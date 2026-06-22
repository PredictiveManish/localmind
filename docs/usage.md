# Usage Guide

All examples use the `lm` alias. The full `localmind` command works identically.

---

## Scan Hardware

Show detailed information about your system's components.

```bash
lm hardware
```

**Example output:**

```
┌─────────────────────────────────────────────────┐
│                 Hardware Information             │
├──────────────┬──────────────────────────────────┤
│ OS           │ Windows 10                        │
│ CPU          │ Intel64 Family 6 Model 158        │
│ Physical ... │ 8                                 │
│ Logical cores│ 16                                │
│ Max freq.    │ 3504 MHz                          │
│ RAM total    │ 32.0 GB                           │
│ RAM avail.   │ 18.5 GB                           │
│ GPU          │ NVIDIA RTX 3060 (12288 MB VRAM)   │
│ Disk total   │ 512.0 GB                          │
│ Disk used    │ 280.0 GB                          │
│ Disk free    │ 232.0 GB                          │
└──────────────┴──────────────────────────────────┘
```

Use this to understand what you're working with before choosing a model.

---

## Get Recommendations

### General Recommendation

Classify your machine and see the recommended parameter range:

```bash
lm recommend
```

**Example output:**

```
Machine tier: Midrange
Recommended parameter range: 7B-14B
RAM: 32.0 GB, VRAM: 12.0 GB
```

### Task-Specific Recommendations

Get model names tailored to a specific use case.

```bash
lm recommend coding
lm recommend writing
lm recommend reasoning
```

**Example output (`lm recommend coding`):**

```
┌──────────────────────────────────────────────────┐
│        Recommendations for coding on your machine │
├────────────────┬──────────────┬──────────────────┤
│ Model          │ Parameters   │ Notes            │
├────────────────┼──────────────┼──────────────────┤
│ codellama:13b  │ 13B          │ Good for coding  │
│ deepseek-...   │ 6.7B         │ Good for coding  │
└────────────────┴──────────────┴──────────────────┘
```

Available tasks:

| Task | Description |
|---|---|
| `coding` | Code generation, completion, debugging assistance |
| `writing` | Creative writing, summarization, content generation |
| `reasoning` | Logic, problem-solving, analytical tasks |

---

## Full Diagnostic

The `doctor` command combines everything — hardware scan, tier classification, warnings, and recommendations — in one report.

```bash
lm doctor
```

**Example output:**

```
╭──────────────────────────────────────╮
│      🩺 LocalMind Doctor Report      │
├──────────────────────────────────────┤
│ Hardware                             │
│   OS: Windows 10                     │
│   CPU: Intel64 ... (8 physical cores)│
│   RAM: 32.0 GB total, 18.5 GB avail │
│   GPU: NVIDIA RTX 3060 (12288 MB)   │
│   Storage: 232 GB free / 512 GB     │
│                                      │
│ Classification                       │
│   Tier: Midrange                     │
│   Recommended model size: 7B-14B     │
│                                      │
│ Warnings                             │
│   ⚠ No dedicated GPU detected. ...   │
│                                      │
│ Recommendations                      │
│   • General rec. (7B-14B): Based on  │
│     your hardware, try models this   │
│     size.                            │
╰──────────────────────────────────────╯
```

It's the best place to start if you're new to the tool.

---

## Search Models

Search the Ollama library for models matching a keyword.

```bash
lm search llama
lm search mistral
lm search coding
```

**Example output:**

```
Searching for models matching 'llama'...

┌────────────────────────────────────────────────┐
│           Ollama Library Search Results         │
├──────────┬─────────────────────┬───────────────┤
│ Name     │ Description         │ Popularity    │
├──────────┼─────────────────────┼───────────────┤
│ llama3   │ Meta Llama 3 8B...  │ 1.2M pulls    │
│ llama2   │ Meta Llama 2 7B...  │ 850K pulls    │
│ ...      │                     │               │
└──────────┴─────────────────────┴───────────────┘
```

Results are sorted by popularity so the most used models appear first.

---

## Inspect a Model

Show metadata for a model you've already pulled locally.

```bash
lm info llama3:8b
```

Requires Ollama to be installed and the model to have been downloaded. Output includes model architecture, parameters, quantization, and system requirements.

---

## Download a Model

Pull a model from the Ollama library.

```bash
lm download llama3:8b
```

If Ollama is not installed, LocalMind will download and install it automatically (with a progress bar), then begin the model pull.

```text
Pulling model llama3:8b…
pulling manifest
pulling 6eeb80ea3609...   0% ▏                   0 B/4.2 GB
pulling 6eeb80ea3609...  12% ██▎               512 MB/4.2 GB
...
```

---

## Built-in Help

```bash
lm help
```

Prints detailed documentation for every command, including explanations, use cases, and examples.
