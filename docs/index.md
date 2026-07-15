# LocalMind

**Understand your hardware and find the best local AI models for your machine.**

[![PyPI](https://img.shields.io/pypi/v/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)
[![Python](https://img.shields.io/pypi/pyversions/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)
[![License](https://img.shields.io/pypi/l/localmind?color=3f51b5&style=flat-square)](https://github.com/predictivemanish/localmind/blob/main/LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)

---

## Why LocalMind?

Here's the problem: you want to run a local LLM. You go to Ollama's library, pick a model, download it, and then… your laptop sounds like a jet engine. Or it crashes. Or it runs at 0.2 tokens per second.

LocalMind solves this. Before you download anything, it scans your hardware, tells you what tier your machine is in, and recommends models that will actually run well on *your* specific setup.

It works across **Windows, macOS, and Linux**. It detects **NVIDIA, AMD, Intel, and Apple Silicon** GPUs. And it knows the difference between a dedicated GPU and unified memory — because a MacBook with 32GB unified memory can run models that a Windows PC with 32GB RAM and no GPU cannot.

## Quick Start

```bash
pip install localmind
lm doctor
```

One command. You get your hardware scan, tier classification, warnings about bottlenecks, and model recommendations. That's it.

## Commands at a Glance

| Command | What it does |
|---|---|
| `lm hardware` | Scan your CPU, RAM, GPU (with VRAM), and disk |
| `lm recommend` | See your tier and what model sizes fit |
| `lm recommend coding` | Models good at code for your hardware |
| `lm recommend writing` | Models good at writing for your hardware |
| `lm recommend reasoning` | Models good at logic for your hardware |
| `lm doctor` | Full diagnostic — everything in one report |
| `lm search <query>` | Search the Ollama library |
| `lm info <model>` | Show metadata for a downloaded model |
| `lm download <model>` | Pull a model (auto-installs Ollama if needed) |
| `lm help` | Detailed help with examples |

All commands work with `lm` (short) or `localmind` (long).

## What's Next?

<div class="grid cards" markdown>

-   :material-download: &nbsp; __Installation__

    ---

    How to install from PyPI or source, verify it works, and set up Ollama.

    [:octicons-arrow-right-24: Installation guide](installation.md)

-   :material-book-open-variant: &nbsp; __Usage Guide__

    ---

    Every command explained with real examples and output walkthroughs.

    [:octicons-arrow-right-24: Usage guide](usage.md)

-   :material-cogs: &nbsp; __Features & Architecture__

    ---

    How GPU detection works across platforms, how the classifier handles unified memory, and how recommendations are generated.

    [:octicons-arrow-right-24: Features & Architecture](features.md)

-   :material-wrench: &nbsp; __Troubleshooting__

    ---

    Common issues, error messages, and how to fix them.

    [:octicons-arrow-right-24: Troubleshooting](troubleshooting.md)

</div>

---

*LocalMind — because choosing a model shouldn't require a PhD in hardware specs.*
