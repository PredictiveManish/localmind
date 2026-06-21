"""Helper functions and shared utilities."""
import sys
from typing import List
from rich.console import Console
from .models import HardwareReport

_console = Console(stderr=True)


def log_warning(msg: str) -> None:
    """Print a warning message to stderr."""
    _console.print(f"[yellow]Warning:[/yellow] {msg}")


def generate_warnings(hw: HardwareReport) -> List[str]:
    """Return a list of hardware/configuration warnings."""
    warnings = []
    if hw.ram.total_gb < 8:
        warnings.append("Low RAM (less than 8 GB). Running models above 4B parameters will be challenging.")
    if not hw.gpus:
        warnings.append("No dedicated GPU detected. Inference will rely on CPU only, which will be slow.")
    if hw.storage.free_gb < 10:
        warnings.append("Low free disk space (<10 GB). Models require several GB each.")
    return warnings