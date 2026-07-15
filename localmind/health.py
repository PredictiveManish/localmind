"""Ollama server health check.

Know the state of your Ollama installation at a glance:
- Is the server running?
- What version?
- How many models loaded?
- GPU utilization?
- Memory usage?
- Any errors?

Usage:
    lm health
    lm health --verbose
"""
from __future__ import annotations
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live

from .ollama_api import (
    list_local_models, list_running_models, get_ollama_version,
    _is_ollama_running, _ensure_ollama_running,
)
from .hardware import get_full_report

console = Console()


def health_check(verbose: bool = False) -> None:
    """Check Ollama server health and display status."""
    # Check if Ollama is running
    is_running = _is_ollama_running()

    if not is_running:
        console.print(Panel(
            "[bold red]Ollama is NOT running[/bold red]\n\n"
            "Start it with:\n"
            "  ollama serve        # foreground\n"
            "  ollama serve &      # background (Linux/macOS)\n"
            "  or use: lm download <model>  # auto-starts",
            title="Ollama Health Check",
            border_style="red"
        ))
        return

    # Get version
    version = get_ollama_version() or "unknown"

    # Get hardware info
    hw = get_full_report()

    # Get local and running models
    local_models = list_local_models()
    running_models = list_running_models()

    # Calculate memory usage
    total_vram = 0.0
    total_ram = hw.ram.total_gb
    for gpu in hw.gpus:
        if gpu.is_unified_memory:
            total_vram += gpu.vram_mb / 1024.0
        else:
            total_vram += gpu.vram_mb / 1024.0

    # Calculate running model memory
    loaded_size = sum(m.model_size for m in running_models) / (1024 ** 3)
    project_size = sum(m.project_size for m in running_models) / (1024 ** 3)

    # Build status
    status_parts = []
    status_parts.append(f"[bold green]✓[/bold green] Ollama is running")
    status_parts.append(f"Version: {version}")
    status_parts.append(f"Local models: {len(local_models)}")
    status_parts.append(f"Running models: {len(running_models)}")

    if running_models:
        for rm in running_models:
            model_size_mb = rm.model_size / (1024 ** 2)
            project_size_mb = rm.project_size / (1024 ** 2)
            status_parts.append(
                f"  • {rm.name}: {model_size_mb:.0f}MB model + {project_size_mb:.0f}MB project"
            )
            if rm.prompt_eval_count > 0:
                status_parts.append(
                    f"    Tokens evaluated: {rm.prompt_eval_count:,} | "
                    f"Generated: {rm.eval_count:,}"
                )

    console.print(Panel(
        "\n".join(status_parts),
        title="Ollama Health Check",
        border_style="green"
    ))

    if verbose:
        _print_verbose_health(hw, local_models, running_models, total_vram, loaded_size)


def _print_verbose_health(hw, local_models, running_models, total_vram, loaded_size):
    """Print detailed health information."""
    console.print()

    # Hardware section
    console.print("[bold underline]Hardware[/bold underline]")
    console.print(f"  CPU: {hw.cpu.name} ({hw.cpu.physical_cores} cores)")
    console.print(f"  RAM: {hw.ram.total_gb:.0f}GB total, {hw.ram.available_gb:.0f}GB available")

    for gpu in hw.gpus:
        vram_str = f"{gpu.vram_mb}MB"
        vendor_str = f" ({gpu.vendor})" if gpu.vendor else ""
        unified_str = " [Unified]" if gpu.is_unified_memory else ""
        console.print(f"  GPU: {gpu.name}{vendor_str} — {vram_str}{unified_str}")

    console.print(f"  Disk: {hw.storage.free_gb:.0f}GB free / {hw.storage.total_gb:.0f}GB")

    # VRAM usage
    console.print()
    console.print("[bold underline]VRAM Usage[/bold underline]")
    if total_vram > 0:
        used_pct = (loaded_size / total_vram * 100) if total_vram > 0 else 0
        color = "green" if used_pct < 80 else "yellow" if used_pct < 95 else "red"
        console.print(f"  Total VRAM: {total_vram:.1f}GB")
        console.print(f"  Used by models: {loaded_size:.1f}GB ({used_pct:.0f}%)")
        console.print(f"  Available: {total_vram - loaded_size:.1f}GB")
        console.print(f"  Status: [{color}]{'Healthy' if used_pct < 80 else 'Warning' if used_pct < 95 else 'Critical'}[/color]")
    else:
        console.print("  No dedicated GPU detected — running on CPU or unified memory")

    # Model library
    console.print()
    console.print("[bold underline]Model Library[/bold underline]")
    if local_models:
        total_disk = sum(m.size for m in local_models) / (1024 ** 3)
        console.print(f"  {len(local_models)} model(s), {total_disk:.1f}GB total")

        table = Table(show_header=False, border_style="dim")
        table.add_column("Name", style="cyan")
        table.add_column("Size", justify="right")
        table.add_column("Status", style="dim")

        for m in local_models:
            size_gb = m.size / (1024 ** 3)
            is_running = any(rm.name == m.name for rm in running_models)
            status = "[green]loaded[/green]" if is_running else "[yellow]idle[/yellow]"
            table.add_row(m.name, f"{size_gb:.1f}GB", status)

        console.print(table)
    else:
        console.print("  No models pulled yet")

    # Recommendations
    console.print()
    console.print("[bold underline]Recommendations[/bold underline]")
    if loaded_size > total_vram * 0.9 and total_vram > 0:
        console.print("  [red]⚠ VRAM nearly full! Models may run slowly or fall back to CPU.[/red]")
        console.print("  Tip: Use smaller quantizations (Q4_0 instead of Q8_0)")
    elif total_vram == 0 and hw.gpus:
        console.print("  [yellow]No dedicated VRAM detected. Models will run on CPU (slower).[/yellow]")

    if hw.storage.free_gb < 20:
        console.print("  [red]⚠ Low disk space! You may not have room for new models.[/red]")

    if not running_models:
        console.print("  [dim]No models currently loaded. Start a chat to load one:[/dim]")
        console.print("    lm chat llama3:8b")
