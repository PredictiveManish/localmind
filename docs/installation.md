# Installation

## Requirements

- **Python 3.11** or later.
- **pip** (Python package manager).
- **Ollama** — optional. Only needed for `lm download` and `lm info`. If you run `lm download` without it, LocalMind will automatically install Ollama for you on Windows, macOS, and Linux.

## Install from PyPI

The recommended way:

```bash
pip install localmind
```

To install with development tools (pytest):

```bash
pip install "localmind[dev]"
```

## Install from Source

```bash
git clone https://github.com/yourusername/localmind.git
cd localmind
pip install -e ".[dev]"
```

The `-e` flag installs it in editable mode — changes you make to the source code take effect immediately.

## Verify Installation

Run the hardware scan to confirm everything works:

```bash
lm hardware
```

You should see a table with your system's CPU, RAM, GPU, and disk information.

```text
┌─────────────────────────────────────────────────┐
│                 Hardware Information             │
├──────────────┬──────────────────────────────────┤
│ OS           │ Windows 10                        │
│ CPU          │ Intel64 Family 6 Model 158        │
│ Physical ... │ 8                                 │
│ Logical cores│ 16                                │
│ RAM total    │ 32.0 GB                           │
│ ...          │                                   │
└──────────────┴──────────────────────────────────┘
```

## Automatic Ollama Setup

When you run `lm download <model>` for the first time, LocalMind checks whether Ollama is installed. If it isn't, it runs the official installer automatically with a progress bar:

- **Windows** — uses the PowerShell installer script.
- **macOS / Linux** — uses the shell installer script.

After installation completes, the model pull begins immediately. You don't need to restart your terminal or install anything manually.

!!! note
    Automatic installation requires an internet connection and administrator/sudo rights. If the automatic install fails, you can always install Ollama manually from [ollama.com](https://ollama.com).
