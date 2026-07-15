"""Local model management.

Ollama is great at pulling models, but managing them is clunky. This module
gives you a proper model library manager:
- List all local models with sizes and quantization
- Delete models you don't need (with disk space saved)
- Find models that fit your hardware
- See disk usage breakdown
- Identify unused models (pulled but never run)

Usage:
    lm models list              # Show all local models
    lm models delete codellama  # Delete a model
    lm models fit               # Show models that fit your hardware
    lm models disk              # Show disk usage by model
"""
from __future__ import annotations
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm

from .ollama_api import list_local_models, delete_model, show_model_details
from .vram import estimate_vram, get_best_quant, format_vram_table
from .hardware import get_full_report
from .models import VRAMEstimate

console = Console()


def list_models(show_details: bool = False) -> None:
    """List all locally pulled models with details."""
    models = list_local_models()

    if not models:
        console.print("[yellow]No models pulled yet. Try: lm download llama3:8b[/yellow]")
        return

    table = Table(title="Local Models", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Quantization", style="yellow")
    table.add_column("Family", style="dim")
    table.add_column("Modified", style="dim")

    for m in models:
        size_gb = m.size / (1024 ** 3) if m.size else 0
        table.add_row(
            m.name,
            f"{size_gb:.1f}GB",
            m.quantization_level or "unknown",
            m.family or "?",
            m.modified_at.split("T")[0] if m.modified_at else "unknown",
        )

    console.print(table)

    # Summary
    total_size = sum(m.size for m in models) / (1024 ** 3)
    console.print(f"\n[dim]Total: {len(models)} model(s), {total_size:.1f} GB used[/dim]")


def delete_model_cmd(model_name: str, force: bool = False) -> None:
    """Delete a local model."""
    models = list_local_models()
    model_names = [m.name for m in models]

    # Check if model exists (exact or prefix match)
    match = None
    for name in model_names:
        if name == model_name or name.startswith(model_name + ":"):
            match = name
            break

    if not match:
        console.print(f"[red]Model '{model_name}' not found.[/red]")
        console.print(f"[dim]Available: {', '.join(model_names[:5])}[/dim]")
        return

    # Get model size before deleting
    model_obj = next(m for m in models if m.name == match)
    size_gb = model_obj.size / (1024 ** 3) if model_obj.size else 0

    if not force:
        if not Confirm.ask(f"Delete [bold]{match}[/bold]? ({size_gb:.1f} GB will be freed)"):
            console.print("[dim]Cancelled.[/dim]")
            return

    success = delete_model(match)
    if success:
        console.print(f"[green]Deleted '{match}' ({size_gb:.1f} GB freed)[/green]")
    else:
        console.print(f"[red]Failed to delete '{match}'.[/red]")


def find_fitting_models() -> None:
    """Find models that fit in your hardware."""
    hw = get_full_report()

    # Calculate available VRAM and RAM
    vram_gb = 0.0
    ram_gb = hw.ram.total_gb
    for gpu in hw.gpus:
        if gpu.is_unified_memory:
            vram_gb += gpu.vram_mb / 1024.0
        else:
            vram_gb += gpu.vram_mb / 1024.0

    console.print(Panel(
        f"[bold]Your hardware:[/bold] {vram_gb:.1f}GB VRAM" +
        (f", {ram_gb:.1f}GB RAM" if not any(g.is_unified_memory for g in hw.gpus) else "") +
        f"\n[Tier {hw.ram.total_gb:.0f}GB RAM]",
        title="Hardware Profile",
        border_style="blue"
    ))

    # Get local models and check which fit
    local_models = list_local_models()
    fitting = []
    not_fitting = []

    for m in local_models:
        est = get_best_quant(m.name, vram_gb, ram_gb)
        if est:
            fitting.append((m, est))
        else:
            not_fitting.append(m)

    # Show fitting models
    if fitting:
        console.print("\n[bold green]✓ Models that fit your hardware:[/bold green]")
        table = Table(show_header=True, header_style="bold green")
        table.add_column("Model", style="cyan")
        table.add_column("Best Quant", style="yellow")
        table.add_column("Size", justify="right")
        table.add_column("VRAM Needed", justify="right")
        table.add_column("RAM Needed", justify="right")

        for m, est in fitting:
            table.add_row(
                m.name,
                est.quantization,
                f"{est.size_gb:.1f}GB",
                f"{est.vram_gb:.1f}GB",
                f"{est.ram_gb:.1f}GB",
            )
        console.print(table)
    else:
        console.print("\n[yellow]No local models fit your hardware.[/yellow]")

    # Show not-fitting models
    if not_fitting:
        console.print("\n[bold red]✗ Models that don't fit:[/bold red]")
        for m in not_fitting:
            size_gb = m.size / (1024 ** 3) if m.size else 0
            console.print(f"  • {m.name} ({size_gb:.1f}GB) — try a smaller quantization")


def show_disk_usage() -> None:
    """Show disk usage breakdown by model."""
    models = list_local_models()

    if not models:
        console.print("[yellow]No models pulled yet.[/yellow]")
        return

    total_size = 0
    table = Table(title="Disk Usage by Model", show_header=True, header_style="bold magenta")
    table.add_column("Model", style="cyan")
    table.add_column("Size", justify="right", style="green")
    table.add_column("Quantization", style="yellow")
    table.add_column("Family", style="dim")

    for m in sorted(models, key=lambda x: x.size, reverse=True):
        size_gb = m.size / (1024 ** 3)
        total_size += size_gb
        table.add_row(
            m.name,
            f"{size_gb:.1f}GB",
            m.quantization_level or "unknown",
            m.family or "?",
        )

    console.print(table)
    console.print(f"\n[dim]Total disk usage: {total_size:.1f} GB across {len(models)} model(s)[/dim]")

    # Storage info
    from .hardware import get_storage_info
    storage = get_storage_info()
    console.print(f"[dim]Free disk space: {storage.free_gb:.1f} GB[/dim]")

    # Warning if low disk
    if storage.free_gb < 20:
        console.print("[yellow]⚠ Low disk space! You may not have room for new models.[/yellow]")


def show_model_fit(model_name: str) -> None:
    """Show VRAM estimates for a specific model."""
    hw = get_full_report()

    vram_gb = 0.0
    ram_gb = hw.ram.total_gb
    for gpu in hw.gpus:
        if gpu.is_unified_memory:
            vram_gb += gpu.vram_mb / 1024.0
        else:
            vram_gb += gpu.vram_mb / 1024.0

    estimates = estimate_vram(model_name, available_vram_gb=vram_gb,
                              available_ram_gb=ram_gb)

    if not estimates:
        console.print(f"[red]Could not estimate VRAM for '{model_name}'.[/red]")
        return

    console.print(Panel(
        f"Hardware: {vram_gb:.1f}GB VRAM" +
        (f", {ram_gb:.1f}GB RAM" if not any(g.is_unified_memory for g in hw.gpus) else ""),
        title=f"VRAM Estimate: {model_name}",
        border_style="blue"
    ))
    console.print()
    console.print(format_vram_table(estimates, vram_gb, ram_gb))

    # Best recommendation
    best = get_best_quant(model_name, vram_gb, ram_gb)
    if best:
        console.print(f"\n[bold green]✓ Best option:[/bold green] {model_name}:{best.quantization} "
                      f"({best.size_gb:.1f}GB, {best.vram_gb:.1f}GB VRAM)")
    else:
        console.print(f"\n[yellow]⚠ No quantization fits your hardware.[/yellow]")
        console.print(f"[dim]Try a smaller model or use CPU inference (slower).[/dim]")
