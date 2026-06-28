"""Interact with Ollama (local installation and library search)."""
from __future__ import annotations
import subprocess
import sys
import json
import shutil
import platform
import time
import re
import urllib.parse
import requests
from typing import List, Optional
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn

from .models import OllamaModel
from .utils import log_warning, _console


def _is_ollama_installed() -> bool:
    """Return True if 'ollama' is in the system PATH."""
    return shutil.which("ollama") is not None


def _install_ollama() -> None:
    """
    Attempt to install Ollama automatically for the current OS.
    Shows a progress bar while downloading and installing.
    Exits the program if installation fails or the platform is unsupported.
    """
    system = platform.system()

    _console.print(
        "[yellow]Starting Ollama download and installation as you don't have it...[/yellow] "
        "[green](this may take several minutes depending on internet speed, also one‑time process)[/green]"
    )

    if system == "Windows":
        cmd = [
            "powershell",
            "-ExecutionPolicy", "Bypass",
            "-Command", "irm https://ollama.com/install.ps1 | iex"
        ]
    elif system in ("Darwin", "Linux"):
        cmd = ["/bin/bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"]
    else:
        log_warning(
            f"Automatic Ollama installation is not supported on {system}. "
            "Please install it manually from https://ollama.com"
        )
        sys.exit(1)

    # Run the installer with a progress bar
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
    except FileNotFoundError as e:
        log_warning(f"Could not start installer: {e}")
        sys.exit(1)

    # Set up a Rich progress bar
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
    )

    task_id = progress.add_task("Installing Ollama...", total=100)

    # Pattern to match a percentage in the output (e.g., "  12.3%")
    pct_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')

    last_pct = 0.0

    with progress:
        try:
            for line in proc.stdout:
                # Look for a percentage value
                match = pct_pattern.search(line)
                if match:
                    try:
                        pct = float(match.group(1))
                        # Only update if the value increased (sometimes the script prints repeated values)
                        if pct >= last_pct:
                            progress.update(task_id, completed=pct)
                            last_pct = pct
                    except ValueError:
                        pass
            proc.wait()

        except KeyboardInterrupt:
            log_warning("Installation interrupted by user.")
            proc.terminate()
            sys.exit(1)

    # Ensure the bar reaches 100% on success
    if proc.returncode == 0:
        progress.update(task_id, completed=100, description="Ollama installed!")
        _console.print("[green]Ollama installation completed successfully![/green]")
    else:
        log_warning(
            f"Ollama installation failed (exit code {proc.returncode}). "
            "Check the output above for details."
        )
        sys.exit(1)


def _ensure_ollama() -> None:
    """
    Check for Ollama; if missing, attempt automatic installation.
    Exits if installation fails or the command is still not found afterwards.
    """
    if _is_ollama_installed():
        return

    _install_ollama()

    if not _is_ollama_installed():
        log_warning(
            "Ollama installation finished but the 'ollama' command is still not "
            "available. You may need to restart your terminal or add it to your PATH."
        )
        sys.exit(1)

    _console.print("[green]Ollama is now ready to use![/green]")


# ────────────────────── public API functions ──────────────────────

def search_ollama_library(query: str) -> List[OllamaModel]:
    """
    Search the Ollama model library using the public API.
    Returns a list of matching models (basic metadata).
    """
    url = f"https://ollama.com/api/library?q={urllib.parse.quote(query)}&sort=popular"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log_warning(f"Search request failed: {e}")
        return []

    models = []
    models_data = data.get("models", {})
    if isinstance(models_data, dict):
        for model_name, model_info in models_data.items():
            if isinstance(model_info, dict):
                models.append(OllamaModel(
                    name=model_info.get("name", model_name),
                    description=model_info.get("description", ""),
                    pulls=model_info.get("pulls"),
                    tags=model_info.get("tags", []),
                    size=model_info.get("model_size"),
                ))
    elif isinstance(models_data, list):
        for item in models_data:
            if isinstance(item, dict):
                models.append(OllamaModel(
                    name=item.get("name", ""),
                    description=item.get("description", ""),
                    pulls=item.get("pulls"),
                    tags=item.get("tags", []),
                    size=item.get("model_size"),
                ))
    return models


def show_model_info(model_name: str) -> Optional[dict]:
    """
    Retrieve model metadata using `ollama show`.
    Returns a JSON dict or None.
    """
    try:
        result = subprocess.run(
            ["ollama", "show", model_name],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    except FileNotFoundError:
        log_warning("Ollama is not installed or not in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        log_warning(f"`ollama show` failed: {e.stderr.strip()}")
        return None
    except json.JSONDecodeError:
        log_warning("Could not parse `ollama show` output.")
        return None


def pull_model(model_name: str) -> None:
    """
    Download (pull) a model using Ollama.
    Automatically installs Ollama if it is not already present.
    Streams the download output to the terminal.
    """
    _console.print(f"Pulling model [bold]{model_name}[/bold]…")
    _ensure_ollama()   # ← Auto‑install Ollama if needed

    proc = None
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout:
            _console.print(line, end="")
        proc.wait()
        if proc.returncode != 0:
            log_warning(f"`ollama pull` exited with code {proc.returncode}")
    except FileNotFoundError:
        log_warning("Ollama is not installed. Please install it from https://ollama.com")
        sys.exit(1)
    except KeyboardInterrupt:
        log_warning("Download interrupted by user.")
        if proc is not None:
            proc.terminate()