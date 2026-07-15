# Installation

## What You Need

- **Python 3.11 or later** — LocalMind won't run on older Python versions
- **pip** — the Python package installer (comes with Python)
- **Ollama** — only needed if you want to download models. LocalMind can install it automatically for you

That's it. No CUDA toolkit, no ROCm drivers, no GPU requirements. LocalMind works on any machine.

## Install from PyPI (Recommended)

```bash
pip install localmind
```

To also install development dependencies (pytest for testing):

```bash
pip install "localmind[dev]"
```

## Install from Source

If you want to modify LocalMind or run it directly from the repository:

```bash
git clone https://github.com/predictivemanish/localmind.git
cd localmind
pip install -e ".[dev]"
```

The `-e` flag installs in "editable" mode — any changes you make to the source code take effect immediately without reinstalling.

## Verify It Works

Run a hardware scan:

```bash
lm hardware
```

You should see a table with your CPU, RAM, GPU, and disk info. If you see this, LocalMind is installed correctly.

```
┌─────────────────────────────────────────────────┐
│              Hardware Information               │
├──────────────┬──────────────────────────────────┤
│ OS           │ Windows 11                       │
│ CPU          │ Intel Core i7-12700H             │
│ Physical cores│ 14                              │
│ Logical cores│ 20                               │
│ Max frequency│ 4700 MHz                         │
│ RAM total    │ 32.0 GB                          │
│ RAM available│ 22.4 GB                          │
│ GPU          │ NVIDIA RTX 3050 (6144 MB VRAM)   │
│ Disk total   │ 512.0 GB                         │
│ Disk used    │ 312.0 GB                         │
│ Disk free    │ 200.0 GB                         │
└──────────────┴──────────────────────────────────┘
```

## What If I Don't Have a GPU?

No problem. LocalMind will detect that you have no dedicated GPU and warn you about CPU-only inference. You can still run small models (1B–7B parameters) on CPU — they'll just be slower.

## What About Ollama?

Ollama is the tool that actually runs the models. LocalMind helps you find the right model; Ollama runs it.

You **don't** need to install Ollama manually. When you run `lm download <model>` for the first time, LocalMind checks if Ollama is installed. If not, it downloads and installs it automatically:

- **Windows**: Runs the official PowerShell installer (`irm https://ollama.com/install.ps1 | iex`)
- **macOS/Linux**: Runs the official shell installer (`curl -fsSL https://ollama.com/install.sh | sh`)

This only happens once. After that, Ollama stays installed and LocalMind just uses it.

!!! note
    Automatic installation requires an internet connection and admin/sudo rights. If it fails, install Ollama manually from [ollama.com](https://ollama.com) and try again.

## Troubleshooting

### "lm" command not found after install

This usually means pip installed to a directory not in your PATH. Try:

```bash
python -m localmind hardware
```

If that works, the issue is just your PATH. Fix it by adding pip's bin directory to PATH, or use `python -m localmind` instead of `lm`.

### "GPUtil not installed" warning

GPUtil is only needed for NVIDIA GPU detection. If you see this warning:
- On **NVIDIA machines**: Run `pip install GPUtil`
- On **non-NVIDIA machines** (Mac, AMD, Intel): Ignore it — LocalMind uses other detection methods

### "No GPU detected" on a machine that has one

This can happen with:
- **AMD GPUs on Linux** without ROCm drivers — try installing ROCm or updating drivers
- **Intel integrated graphics** — LocalMind should detect these, but if it doesn't, check that your graphics drivers are up to date
- **Apple Silicon** — LocalMind uses `system_profiler`, which should always work on macOS

Run `lm hardware` to see what was detected. If something seems wrong, check the [troubleshooting guide](troubleshooting.md).
