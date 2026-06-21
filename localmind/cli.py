"""
LocalMind CLI – Typer application.
Usage: localmind [command] [options]
"""
from __future__ import annotations
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from .hardware import get_full_report
from .classifier import classify_machine
from .recommendations import general_recommendation, task_recommendations
from .doctor import generate_doctor_report
from .ollama_api import search_ollama_library, show_model_info, pull_model

app = typer.Typer(
    help="LocalMind – find the best local AI models for your hardware.",
    no_args_is_help=True,
)
console = Console()


# ──────────────────────────────────────────────────────────────
# Custom help command
# ──────────────────────────────────────────────────────────────
@app.command("help")
def help_command():
    """
    Display detailed help for all LocalMind commands with explanations.
    
    Usage:
        localmind help
    """
    help_text = """
# 🧠 LocalMind Help

LocalMind helps you **understand your hardware** and **find the best local AI models** that fit your machine.
All commands are also available using the `lm` alias.

---

## Commands

### `localmind hardware` (or `lm hardware`)

**What it does:**  
Scans your system and displays detailed information about your CPU, RAM, GPU (if any), VRAM, disk space, and operating system.

**When to use it:**  
When you want to see exactly what hardware you're working with before choosing an AI model.

**Example:**  
localmind hardware

---

### `localmind recommend` (or `lm recommend`)

**What it does:**  
Analyzes your hardware and classifies your machine into a tier:
- **Tiny** – very limited hardware (Raspberry Pi, old laptops)
- **Entry** – basic machines (8GB RAM, integrated graphics)
- **Midrange** – decent setups (16GB RAM, entry-level GPU)
- **High-End** – powerful workstations (32GB+ RAM, 8GB+ VRAM)
- **Enthusiast** – top-tier rigs (64GB+ RAM, 16GB+ VRAM)

Then recommends a **parameter size range** (e.g., 7B-8B) that should run comfortably.

**When to use it:**  
As a first step to understand what class of models your hardware can handle.

**Example:**  

---

### `localmind recommend` (or `lm recommend`)

**What it does:**  
Analyzes your hardware and classifies your machine into a tier:
- **Tiny** – very limited hardware (Raspberry Pi, old laptops)
- **Entry** – basic machines (8GB RAM, integrated graphics)
- **Midrange** – decent setups (16GB RAM, entry-level GPU)
- **High-End** – powerful workstations (32GB+ RAM, 8GB+ VRAM)
- **Enthusiast** – top-tier rigs (64GB+ RAM, 16GB+ VRAM)

Then recommends a **parameter size range** (e.g., 7B-8B) that should run comfortably.

**When to use it:**  
As a first step to understand what class of models your hardware can handle.

**Example:**  
localmind recommend

---

### `localmind recommend coding` (or `lm recommend coding`)

**What it does:**  
Suggests specific models optimized for **coding tasks** (code generation, completion, debugging) based on your hardware tier.

**When to use it:**  
When you want an AI assistant for programming and want models known to perform well on code.

**Example:**  
localmind recommend coding


---

### `localmind recommend writing` (or `lm recommend writing`)

**What it does:**  
Suggests models optimized for **writing tasks** (creative writing, summarization, content generation).

**When to use it:**  
When you need help with text generation, editing, or content creation.

**Example:**  
localmind recommend writing

---

### `localmind recommend reasoning` (or `lm recommend reasoning`)

**What it does:**  
Suggests models optimized for **reasoning tasks** (logic, problem-solving, analysis).

**When to use it:**  
When you need strong analytical or logical reasoning capabilities.

**Example:**  

localmind recommend reasoning



---

### `localmind doctor` (or `lm doctor`)

**What it does:**  
Runs a **full diagnostic** on your system:
- Hardware summary
- Machine classification
- Warnings (low RAM, no GPU, low disk space)
- General model recommendations

**When to use it:**  
When you want a complete picture of your system's readiness for running local AI models, including any potential issues.

**Example:**  

localmind doctor

---

### `localmind search <query>` (or `lm search <query>`)

**What it does:**  
Searches the **Ollama model library** for models matching your query. Shows model names, descriptions, and download popularity.

**When to use it:**  
When you want to discover new models or find a specific model by name or keyword.

**Examples:**  

localmind search llama
localmind search coding
localmind search mistral


---

### `localmind info <model>` (or `lm info <model>`)

**What it does:**  
Displays detailed **metadata** about a locally available Ollama model (size, parameters, quantization, etc.).  
Requires the model to be already downloaded.

**When to use it:**  
When you want to inspect a model you've already pulled to understand its resource requirements or configuration.

**Example:**  

localmind info llama3:8b


---

### `localmind download <model>` (or `lm download <model>`)

**What it does:**  
Downloads (pulls) a model from the Ollama library using the `ollama pull` command.  
Streams the download progress to your terminal.

**Requires:** Ollama installed and running (get it from https://ollama.com).

**When to use it:**  
After you've found a model you want to try, use this to download it.

**Example:**  

localmind download llama3:8b


---

## Tips

- Use `localmind doctor` first to understand your hardware capabilities.
- Use `localmind recommend` to see what parameter range fits your machine.
- Use `localmind recommend coding/writing/reasoning` for task-specific suggestions.
- Use `localmind search <query>` to explore the Ollama library.
- Use `localmind download <model>` to pull a model you like.

## Aliases

All commands work with both `localmind` and the shorter `lm`:

lm hardware
lm recommend coding
lm doctor
lm search llama3


---

**Need more help?** Visit https://ollama.com/library to browse all available models.
"""
    
    md = Markdown(help_text)
    console.print(md)


# ──────────────────────────────────────────────────────────────
# Hardware command
# ──────────────────────────────────────────────────────────────
@app.command()
def hardware():
    """Display detailed hardware information."""
    hw = get_full_report()
    table = Table(title="Hardware Information", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Details", style="green")

    table.add_row("OS", hw.os)
    table.add_row("CPU", hw.cpu.name)
    table.add_row("Physical cores", str(hw.cpu.physical_cores))
    table.add_row("Logical cores", str(hw.cpu.logical_cores))
    table.add_row("Max frequency", f"{hw.cpu.max_frequency_mhz} MHz")
    table.add_row("RAM total", f"{hw.ram.total_gb} GB")
    table.add_row("RAM available", f"{hw.ram.available_gb} GB")

    if hw.gpus:
        for gpu in hw.gpus:
            table.add_row("GPU", f"{gpu.name} ({gpu.vram_mb} MB VRAM)")
    else:
        table.add_row("GPU", "None detected")

    table.add_row("Disk total", f"{hw.storage.total_gb} GB")
    table.add_row("Disk used", f"{hw.storage.used_gb} GB")
    table.add_row("Disk free", f"{hw.storage.free_gb} GB")

    console.print(table)


# ──────────────────────────────────────────────────────────────
# Recommend command
# ──────────────────────────────────────────────────────────────
@app.command()
def recommend(task: Optional[str] = typer.Argument(None, help="Sub-task: coding, writing, reasoning")):
    """
    Recommend models based on your hardware.
    Without a task, shows your hardware tier and recommended parameter range.
    With a task, suggests specific models for coding/writing/reasoning.
    """
    hw = get_full_report()
    if task:
        task = task.lower()
        if task not in ("coding", "writing", "reasoning"):
            console.print(f"[red]Unknown task '{task}'. Choose from coding, writing, reasoning.[/red]")
            raise typer.Exit(1)
        recs = task_recommendations(hw, task)
        console.print(Panel(f"Recommendations for [bold]{task}[/bold] on your machine", style="bold blue"))
        table = Table("Model", "Parameters", "Notes", title="Task-specific Models")
        for r in recs:
            table.add_row(r.name, r.parameter_size, r.notes)
        console.print(table)
    else:
        mc = general_recommendation(hw)
        console.print(f"[bold]Machine tier:[/bold] {mc.tier}")
        console.print(f"[bold]Recommended parameter range:[/bold] {mc.recommended_param_range}")
        console.print(f"[dim]{mc.rationale}[/dim]")


# ──────────────────────────────────────────────────────────────
# Doctor command
# ──────────────────────────────────────────────────────────────
@app.command()
def doctor():
    """Run a full diagnostic and display a report."""
    report = generate_doctor_report()
    console.print(Panel("🩺 LocalMind Doctor Report", style="bold green"))
    
    # Hardware summary
    hw = report.hardware
    console.print("[bold underline]Hardware[/bold underline]")
    console.print(f"OS: {hw.os}")
    console.print(f"CPU: {hw.cpu.name} ({hw.cpu.physical_cores} physical cores)")
    console.print(f"RAM: {hw.ram.total_gb} GB total, {hw.ram.available_gb} GB available")
    if hw.gpus:
        for gpu in hw.gpus:
            console.print(f"GPU: {gpu.name} ({gpu.vram_mb} MB)")
    else:
        console.print("GPU: None")
    console.print(f"Storage: {hw.storage.free_gb} GB free out of {hw.storage.total_gb} GB")

    # Classification
    mc = report.classification
    console.print(f"\n[bold underline]Classification[/bold underline]")
    console.print(f"Tier: [bold cyan]{mc.tier}[/bold cyan]")
    console.print(f"Recommended model size: {mc.recommended_param_range}")

    # Warnings
    if report.warnings:
        console.print("\n[bold underline]Warnings[/bold underline]")
        for w in report.warnings:
            console.print(f"⚠️  [yellow]{w}[/yellow]")

    # Recommendations
    console.print("\n[bold underline]Recommendations[/bold underline]")
    for r in report.recommendations:
        console.print(f"• {r.name} ({r.parameter_size}): {r.notes}")


# ──────────────────────────────────────────────────────────────
# Search command
# ──────────────────────────────────────────────────────────────
@app.command()
def search(query: str):
    """Search the Ollama model library."""
    console.print(f"Searching for models matching '[italic]{query}[/italic]'...\n")
    models = search_ollama_library(query)
    if not models:
        console.print("[yellow]No models found or search failed.[/yellow]")
        return
    table = Table(title="Ollama Library Search Results", show_lines=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Popularity")
    for m in models:
        pulls = str(m.pulls) if m.pulls else "N/A"
        table.add_row(m.name, m.description[:100] + "...", pulls)
    console.print(table)


# ──────────────────────────────────────────────────────────────
# Info command
# ──────────────────────────────────────────────────────────────
@app.command()
def info(model: str):
    """Display metadata for a locally available Ollama model."""
    data = show_model_info(model)
    if not data:
        console.print("[red]Could not retrieve model info. Is Ollama installed and the model pulled?[/red]")
        return
    # Pretty print JSON fields
    console.print(f"[bold]Model: {data.get('name', model)}[/bold]")
    for key, value in data.items():
        console.print(f"{key}: {value}")


# ──────────────────────────────────────────────────────────────
# Download command
# ──────────────────────────────────────────────────────────────
@app.command()
def download(model: str):
    """
    Download (pull) a model using Ollama.
    This runs `ollama pull <model>` and streams the output.
    """
    console.print(f"Pulling model [bold]{model}[/bold]...")
    pull_model(model)


if __name__ == "__main__":
    app()