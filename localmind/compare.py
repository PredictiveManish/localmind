"""Side-by-side model comparison.

Compare any two models on the metrics that actually matter:
- Parameter count
- Disk size at each quantization
- Estimated VRAM/RAM requirements
- Known strengths (coding, reasoning, writing)
- Popularity (pull count)

Usage:
    lm compare llama3:8b mistral:7b
    lm compare codellama:13b deepseek-coder:6.7b
"""
from __future__ import annotations
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from .ollama_api import search_ollama_library, list_local_models, show_model_details
from .vram import estimate_vram, get_best_quant, format_vram_table
from .hardware import get_full_report
from .models import VRAMEstimate

console = Console()


def compare_models(model_a: str, model_b: str) -> None:
    """Compare two models side by side."""
    hw = get_full_report()

    # Calculate available VRAM and RAM
    vram_gb = 0.0
    ram_gb = hw.ram.total_gb
    for gpu in hw.gpus:
        if gpu.is_unified_memory:
            vram_gb += gpu.vram_mb / 1024.0
        else:
            vram_gb += gpu.vram_mb / 1024.0

    # Get VRAM estimates for both
    est_a = estimate_vram(model_a, available_vram_gb=vram_gb, available_ram_gb=ram_gb)
    est_b = estimate_vram(model_b, available_vram_gb=vram_gb, available_ram_gb=ram_gb)

    # Get best quant for both
    best_a = get_best_quant(model_a, vram_gb, ram_gb) if est_a else None
    best_b = get_best_quant(model_b, vram_gb, ram_gb) if est_b else None

    # Search for pull counts
    models_a = search_ollama_library(model_a.split(":")[0])
    models_b = search_ollama_library(model_b.split(":")[0])
    pulls_a = _find_pulls(models_a, model_a)
    pulls_b = _find_pulls(models_b, model_b)

    # Check if local
    local = list_local_models()
    local_names = [m.name for m in local]
    def _is_local(model_name: str) -> bool:
        if model_name in local_names:
            return True
        # Check if any local model is a prefix of the queried model
        for n in local_names:
            if model_name.startswith(n + ":") or n.startswith(model_name.split(":")[0] + ":"):
                return True
        return False
    is_local_a = _is_local(model_a)
    is_local_b = _is_local(model_b)

    # Build comparison table
    table = Table(title=f"Model Comparison: {model_a} vs {model_b}", show_header=True,
                  header_style="bold magenta")
    table.add_column("Metric", style="cyan", width=20)
    table.add_column(model_a, style="green", width=18)
    table.add_column(model_b, style="blue", width=18)

    # Parameter count
    params_a = _extract_params(model_a)
    params_b = _extract_params(model_b)
    table.add_row("Parameters", f"{params_a:.1f}B", f"{params_b:.1f}B")

    # Best quantization that fits
    best_quant_a = best_a.quantization if best_a else "N/A"
    best_quant_b = best_b.quantization if best_b else "N/A"
    table.add_row("Best Fit Quant", best_quant_a, best_quant_b)

    # Size at best quant
    size_a = f"{best_a.size_gb:.1f}GB" if best_a else "N/A"
    size_b = f"{best_b.size_gb:.1f}GB" if best_b else "N/A"
    table.add_row("Size (best quant)", size_a, size_b)

    # VRAM needed
    vram_a = f"{best_a.vram_gb:.1f}GB" if best_a else "N/A"
    vram_b = f"{best_b.vram_gb:.1f}GB" if best_b else "N/A"
    table.add_row("VRAM Needed", vram_a, vram_b)

    # RAM needed (CPU inference)
    ram_a = f"{best_a.ram_gb:.1f}GB" if best_a else "N/A"
    ram_b = f"{best_b.ram_gb:.1f}GB" if best_b else "N/A"
    table.add_row("RAM Needed (CPU)", ram_a, ram_b)

    # Fits in hardware
    fits_a = "[green]✓ Yes[/green]" if best_a else "[red]✗ No[/red]"
    fits_b = "[green]✓ Yes[/green]" if best_b else "[red]✗ No[/red]"
    table.add_row(f"Fits in your hardware ({vram_gb:.1f}GB VRAM)", fits_a, fits_b)

    # Pull count (popularity)
    table.add_row("Popularity", f"{_format_pulls(pulls_a)}", f"{_format_pulls(pulls_b)}")

    # Local status
    local_a = "[green]✓ Local[/green]" if is_local_a else "[yellow]○ Remote[/yellow]"
    local_b = "[green]✓ Local[/green]" if is_local_b else "[yellow]○ Remote[/yellow]"
    table.add_row("Downloaded", local_a, local_b)

    # Recommended task
    table.add_row("Good for", _best_task(model_a), _best_task(model_b))

    console.print(table)

    # VRAM breakdown for both
    console.print()
    if est_a:
        console.print(f"[bold]VRAM breakdown — {model_a}:[/bold]")
        console.print(format_vram_table(est_a, vram_gb, ram_gb))
    if est_b:
        console.print()
        console.print(f"[bold]VRAM breakdown — {model_b}:[/bold]")
        console.print(format_vram_table(est_b, vram_gb, ram_gb))

    # Recommendation
    console.print()
    if best_a and best_b:
        if best_a.size_gb < best_b.size_gb:
            console.print(f"[bold green]→ If hardware is limited:[/bold green] "
                          f"{model_a} ({best_a.size_gb:.1f}GB) fits easier")
        elif best_b.size_gb < best_a.size_gb:
            console.print(f"[bold green]→ If hardware is limited:[/bold green] "
                          f"{model_b} ({best_b.size_gb:.1f}GB) fits easier")
        else:
            console.print(f"[bold green]→ Both fit:[/bold green] pick based on your use case")

        if pulls_a > pulls_b:
            console.print(f"[dim]Note: {model_a} is more popular ({pulls_a:,} vs {pulls_b:,} pulls)[/dim]")
        elif pulls_b > pulls_a:
            console.print(f"[dim]Note: {model_b} is more popular ({pulls_b:,} vs {pulls_a:,} pulls)[/dim]")
    elif best_a:
        console.print(f"[bold green]→ {model_a} fits your hardware. {model_b} does not.[/bold green]")
    elif best_b:
        console.print(f"[bold green]→ {model_b} fits your hardware. {model_a} does not.[/bold green]")
    else:
        console.print(f"[bold red]→ Neither model fits your hardware ({vram_gb:.1f}GB VRAM).[/bold red]")
        console.print(f"[dim]Try smaller models (7B or less) or use CPU inference.[/dim]")


def _extract_params(model_name: str) -> float:
    """Extract parameter count from model name."""
    import re
    match = re.search(r':(\d+\.?\d*)b', model_name, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 0.0


def _find_pulls(models: list, model_name: str) -> Optional[int]:
    """Find pull count for a specific model from search results."""
    base_name = model_name.split(":")[0]
    for m in models:
        if m.name == model_name or m.name == base_name:
            return m.pulls
    return None


def _format_pulls(pulls: Optional[int]) -> str:
    """Format pull count for display."""
    if not pulls:
        return "N/A"
    if pulls >= 1_000_000:
        return f"{pulls / 1_000_000:.1f}M"
    if pulls >= 1_000:
        return f"{pulls / 1_000:.1f}K"
    return str(pulls)


def _best_task(model_name: str) -> str:
    """Guess the best task for a model based on its name."""
    name = model_name.lower().split(":")[0]

    coding_keywords = ["coder", "code", "deepseek-coder", "codellama"]
    writing_keywords = ["write", "narrative", "story"]
    reasoning_keywords = ["reason", "logic", "math", "qwq", "o1"]

    for kw in coding_keywords:
        if kw in name:
            return "Coding"
    for kw in reasoning_keywords:
        if kw in name:
            return "Reasoning"
    for kw in writing_keywords:
        if kw in name:
            return "Writing"

    # Default based on family
    if "llama" in name or "mistral" in name or "gemma" in name:
        return "General"
    if "phi" in name:
        return "General"
    if "qwen" in name:
        return "General"

    return "General"
