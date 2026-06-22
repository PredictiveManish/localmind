# LocalMind

**Understand your hardware and find the best local AI models for your machine.**

[![PyPI](https://img.shields.io/pypi/v/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)
[![Python](https://img.shields.io/pypi/pyversions/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)
[![License](https://img.shields.io/pypi/l/localmind?color=3f51b5&style=flat-square)](https://github.com/yourusername/localmind/blob/main/LICENSE)
[![PyPI Downloads](https://img.shields.io/pypi/dm/localmind?color=3f51b5&style=flat-square)](https://pypi.org/project/localmind/)

---

## Why LocalMind?

Running large language models locally is exciting — but figuring out *which models your hardware can actually handle* is a guessing game. LocalMind takes the guesswork out:

- **Scan your system** — CPU, RAM, GPU (with VRAM), and disk space in one command.
- **Instant tier classification** — see exactly where your machine sits, from Tiny to Enthusiast.
- **Smart model recommendations** — get model names and parameter sizes that will run well on *your* hardware.
- **Ollama integration** — search, inspect, and download models from the Ollama library without leaving your terminal.

## Quick Start

```bash
pip install localmind
lm doctor
```

That's it. The `doctor` command runs a full diagnostic — hardware scan, tier classification, warnings, and model recommendations in a single report.

## Commands at a Glance

| Command | Description |
|---|---|
| `lm hardware` | Display detailed hardware information (CPU, RAM, GPU, disk) |
| `lm recommend` | Classify your machine and show the recommended parameter size range |
| `lm recommend <task>` | Suggest specific models for `coding`, `writing`, or `reasoning` |
| `lm doctor` | Full diagnostic: hardware + tier + warnings + recommendations |
| `lm search <query>` | Search the Ollama model library by keyword |
| `lm info <model>` | Show metadata of a locally pulled Ollama model |
| `lm download <model>` | Pull a model from Ollama (auto-installs Ollama if missing) |
| `lm help` | Print detailed help with examples |

All commands work with both `localmind` and the shorter `lm` alias.

## Next Steps

<div class="grid cards" markdown>

-   :material-download: &nbsp; __Installation__

    ---

    Prerequisites, pip install, source install, and verification.

    [:octicons-arrow-right-24: Installation guide](installation.md)

-   :material-book-open-variant: &nbsp; __Usage Guide__

    ---

    Detailed walkthrough for every command with examples and output.

    [:octicons-arrow-right-24: Usage guide](usage.md)

-   :material-cogs: &nbsp; __Features & Architecture__

    ---

    How hardware detection, tier classification, and recommendations work under the hood.

    [:octicons-arrow-right-24: Features & Architecture](features.md)

</div>

---

*Made with LocalMind — because choosing a model shouldn't require a PhD in hardware specs.*
