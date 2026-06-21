"""Interact with Ollama (local installation and library search)."""
from __future__ import annotations
import subprocess
import sys
import json
import requests
from typing import List, Optional
from .models import OllamaModel
from .utils import log_warning, _console


def search_ollama_library(query: str) -> List[OllamaModel]:
    """
    Search the Ollama model library using the public API.
    Returns a list of matching models (basic metadata).
    """
    url = f"https://ollama.com/api/library?q={query}&sort=popular"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log_warning(f"Search request failed: {e}")
        return []

    models = []
    for item in data.get("models", []):
        models.append(OllamaModel(
            name=item.get("name", ""),
            description=item.get("description", ""),
            pulls=item.get("pulls"),
            tags=item.get("tags", []),
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
        # The output is JSON
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
    Pull a model using `ollama pull`. Streams output to the terminal.
    """
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
        proc.terminate()