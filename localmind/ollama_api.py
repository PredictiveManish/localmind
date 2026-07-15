"""Ollama HTTP API client — talks to ollama running on localhost:11434.

Ollama exposes a REST API at http://localhost:11434. This module wraps all
endpoints so LocalMind can control Ollama without shelling out to subprocess.

Endpoints used:
  GET  /api/tags          — list locally pulled models
  GET  /api/ps            — running models + memory usage
  GET  /api/version       — Ollama server version
  POST /api/pull          — download a model (streaming)
  POST /api/push          — upload a model
  POST /api/show          — model metadata
  POST /api/generate      — single-turn generation (streaming)
  POST /api/chat          — multi-turn chat (streaming)
  POST /api/copy          — copy a model
  DELETE /api/delete     — delete a model
  POST /api/tags         — (same as GET)

Subprocess functions are kept for operations not exposed via HTTP API
(e.g., ollama show full JSON, ollama install).
"""
from __future__ import annotations
import subprocess
import sys
import json
import shutil
import platform
import re
import urllib.parse
import requests
from typing import List, Optional, Dict, Any, Iterator
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn, TimeRemainingColumn

from .models import OllamaModel, OllamaLocalModel, OllamaRunningModel, OllamaChatMessage
from .utils import log_warning, _console

OLLAMA_HOST = "http://localhost:11434"


# ────────────────────── connection helpers ──────────────────────

def _http_request(method: str, path: str, json_data: Optional[Dict] = None,
                  stream: bool = False, timeout: int = 120) -> requests.Response:
    """Make an HTTP request to the local Ollama server."""
    url = f"{OLLAMA_HOST}{path}"
    try:
        resp = requests.request(method, url, json=json_data, stream=stream, timeout=timeout)
        resp.raise_for_status()
        return resp
    except requests.ConnectionError:
        log_warning("Cannot connect to Ollama. Is it running? Start it with: ollama serve")
        raise
    except requests.Timeout:
        log_warning(f"Request to {url} timed out after {timeout}s")
        raise
    except requests.RequestException as e:
        log_warning(f"HTTP request failed: {e}")
        raise


def _is_ollama_running() -> bool:
    """Check if Ollama server is responding on localhost:11434."""
    try:
        requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        return True
    except requests.RequestException:
        return False


def _ensure_ollama_running() -> bool:
    """
    Check if Ollama is running. If not, try to start it.
    Returns True if Ollama is available, False otherwise.
    """
    if _is_ollama_running():
        return True

    # Try to start ollama serve in the background
    system = platform.system()
    proc = None
    try:
        proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # Wait for it to come up
        for _ in range(10):
            if _is_ollama_running():
                return True
            import time
            time.sleep(1)
    except FileNotFoundError:
        log_warning("Ollama is not installed. Install it from https://ollama.com")
        return False
    finally:
        if proc and proc.poll() is None:
            proc.terminate()

    log_warning("Ollama failed to start. Run 'ollama serve' manually.")
    return False


# ────────────────────── installation helpers (subprocess) ──────────────────────

def _is_ollama_installed() -> bool:
    """Return True if 'ollama' binary is in PATH."""
    return shutil.which("ollama") is not None


def _install_ollama() -> None:
    """Attempt to install Ollama automatically for the current OS."""
    system = platform.system()

    _console.print(
        "[yellow]Starting Ollama download and installation...[/yellow] "
        "[green](one-time process)[/green]"
    )

    if system == "Windows":
        cmd = [
            "powershell", "-ExecutionPolicy", "Bypass",
            "-Command", "irm https://ollama.com/install.ps1 | iex"
        ]
    elif system in ("Darwin", "Linux"):
        cmd = ["/bin/bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"]
    else:
        log_warning(f"Automatic Ollama installation is not supported on {system}.")
        sys.exit(1)

    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1,
        )
    except FileNotFoundError as e:
        log_warning(f"Could not start installer: {e}")
        sys.exit(1)

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=_console,
    )
    task_id = progress.add_task("Installing Ollama...", total=100)
    pct_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*%')
    last_pct = 0.0

    with progress:
        try:
            for line in proc.stdout:
                match = pct_pattern.search(line)
                if match:
                    try:
                        pct = float(match.group(1))
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

    if proc.returncode == 0:
        progress.update(task_id, completed=100, description="Ollama installed!")
        _console.print("[green]Ollama installation completed successfully![/green]")
    else:
        log_warning(f"Ollama installation failed (exit code {proc.returncode}).")
        sys.exit(1)


def _ensure_ollama() -> None:
    """Check for Ollama binary; auto-install if missing."""
    if _is_ollama_installed():
        return
    _install_ollama()
    if not _is_ollama_installed():
        log_warning("Ollama installation finished but 'ollama' command is not available.")
        sys.exit(1)
    _console.print("[green]Ollama is now ready to use![/green]")


# ────────────────────── HTTP API: model listing ──────────────────────

def list_local_models() -> List[OllamaLocalModel]:
    """
    List all models pulled locally via the Ollama HTTP API.

    Returns OllamaLocalModel with name, size, digest, and details
    (parameter_size, quantization_level, format, family).
    """
    try:
        resp = _http_request("GET", "/api/tags")
        data = resp.json()
    except requests.RequestException:
        return []

    models = []
    for item in data.get("models", []):
        details = item.get("details", {})
        models.append(OllamaLocalModel(
            name=item.get("name", ""),
            size=item.get("size", 0),
            digest=item.get("digest", ""),
            modified_at=item.get("modified_at", ""),
            parameter_size=details.get("parameter_size", ""),
            quantization_level=details.get("quantization_level", ""),
            format=details.get("format", ""),
            family=details.get("family", ""),
            families=details.get("families", []),
        ))
    return models


# ────────────────────── HTTP API: running models ──────────────────────

def list_running_models() -> List[OllamaRunningModel]:
    """
    Show models currently loaded in Ollama's memory.

    Returns OllamaRunningModel with model name, total/prompt/decode timings,
    and load/unload status.
    """
    try:
        resp = _http_request("GET", "/api/ps")
        data = resp.json()
    except requests.RequestException:
        return []

    # API returns {"models": [...]} or a single model dict
    models_data = data.get("models", [])
    if not models_data and isinstance(data, dict):
        models_data = [data]

    running = []
    for item in models_data:
        running.append(OllamaRunningModel(
            model=item.get("model", ""),
            name=item.get("name", ""),
            digest=item.get("digest", ""),
            model_size=item.get("model_size", 0),
            project_size=item.get("project_size", 0),
            load_status=item.get("load_status", ""),
            prompt_eval_count=item.get("prompt_eval_count", 0),
            prompt_eval_duration=item.get("prompt_eval_duration", 0),
            eval_count=item.get("eval_count", 0),
            eval_duration=item.get("eval_duration", 0),
        ))
    return running


# ────────────────────── HTTP API: version ──────────────────────

def get_ollama_version() -> Optional[str]:
    """Return the Ollama server version string."""
    try:
        resp = _http_request("GET", "/api/version")
        data = resp.json()
        return data.get("version", "unknown")
    except requests.RequestException:
        return None


# ────────────────────── HTTP API: show model details ──────────────────────

def show_model_details(model_name: str) -> Optional[Dict[str, Any]]:
    """
    Get full model metadata via HTTP API (faster than subprocess ollama show).

    Returns the raw JSON dict from the API, including modelfile, parameters,
    messages, template, system, license, and more.
    """
    try:
        resp = _http_request("POST", "/api/show", json_data={"name": model_name})
        return resp.json()
    except requests.RequestException:
        return None


# ────────────────────── HTTP API: generate (single-turn) ──────────────────────

def generate(model_name: str, prompt: str, system: Optional[str] = None,
             template: Optional[str] = None, context: Optional[List[int]] = None,
             options: Optional[Dict[str, Any]] = None,
             stream: bool = True) -> Iterator[str]:
    """
    Generate a response from a model (single turn, no chat history).

    Yields text chunks as they arrive (streaming).
    If stream=False, returns the full response as a string.

    Parameters:
        model_name: e.g. "llama3:8b"
        prompt: the user prompt
        system: system prompt (optional)
        template: custom template (optional)
        context: conversation context from a previous call (optional)
        options: extra options like temperature, top_k, top_p, etc.
        stream: whether to stream output (default True)
    """
    payload = {"model": model_name, "prompt": prompt, "stream": stream}
    if system:
        payload["system"] = system
    if template:
        payload["template"] = template
    if context:
        payload["context"] = context
    if options:
        payload["options"] = options

    try:
        resp = _http_request("POST", "/api/generate", json_data=payload, stream=True)
        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if stream:
                    yield chunk.get("response", "")
                if chunk.get("done", False):
                    break
        if not stream:
            # Collect all chunks
            full = ""
            for chunk_text in generate(model_name, prompt, system, template, context, options, stream=True):
                full += chunk_text
            yield full
    except requests.RequestException:
        yield "[error: failed to connect to Ollama]"


# ────────────────────── HTTP API: chat (multi-turn) ──────────────────────

def chat(model_name: str, messages: List[OllamaChatMessage],
         options: Optional[Dict[str, Any]] = None,
         stream: bool = True,
         keep_alive: Optional[str] = None) -> Iterator[str]:
    """
    Multi-turn chat with a model via the Ollama HTTP API.

    Yields text chunks as they arrive (streaming).

    Parameters:
        model_name: e.g. "llama3:8b"
        messages: list of OllamaChatMessage (role + content)
        options: extra options (temperature, top_k, top_p, num_ctx, etc.)
        stream: whether to stream output (default True)
        keep_alive: how long to keep the model loaded ("5m", "1h", "-1" = forever)
    """
    payload = {
        "model": model_name,
        "messages": [msg.model_dump() for msg in messages],
        "stream": stream,
    }
    if options:
        payload["options"] = options
    if keep_alive:
        payload["keep_alive"] = keep_alive

    try:
        resp = _http_request("POST", "/api/chat", json_data=payload, stream=True)
        for line in resp.iter_lines():
            if line:
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if stream:
                    msg_data = chunk.get("message", {})
                    yield msg_data.get("content", "")
                if chunk.get("done", False):
                    break
    except requests.RequestException:
        yield "[error: failed to connect to Ollama]"


# ────────────────────── HTTP API: delete model ──────────────────────

def delete_model(model_name: str) -> bool:
    """Delete a locally pulled model."""
    try:
        _http_request("DELETE", f"/api/delete", json_data={"name": model_name})
        return True
    except requests.RequestException:
        log_warning(f"Failed to delete model '{model_name}'.")
        return False


# ────────────────────── HTTP API: copy model ──────────────────────

def copy_model(source: str, destination: str) -> bool:
    """Copy a model (e.g., to create a fine-tuned variant)."""
    try:
        _http_request("POST", "/api/copy", json_data={"source": source, "destination": destination})
        return True
    except requests.RequestException:
        log_warning(f"Failed to copy '{source}' to '{destination}'.")
        return False


# ────────────────────── HTTP API: pull model (streaming) ──────────────────────

def pull_model_stream(model_name: str, quiet: bool = False) -> bool:
    """
    Download a model via the HTTP API with a clean Rich progress bar.

    Shows a bar with percentage, elapsed time, and time remaining.
    Returns True if the pull succeeded, False otherwise.
    """
    if not _ensure_ollama_running():
        raise RuntimeError("Ollama is not running")

    payload = {"name": model_name, "stream": True}
    total_size = 0
    last_status = ""
    pull_error = False
    try:
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=_console,
        ) as progress:
            task_id = progress.add_task("pulling", total=0)
            resp = _http_request("POST", "/api/pull", json_data=payload, stream=True)
            for line in resp.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    status = chunk.get("status", "")
                    total = chunk.get("total", 0)
                    completed = chunk.get("completed", 0)
                    if total and total > 0:
                        total_size = total
                        progress.update(task_id, total=total_size)
                        if status != last_status:
                            last_status = status
                    if not quiet:
                        progress.update(task_id, completed=completed, description=status or "pulling")
                    if chunk.get("error"):
                        console.print(f"[red]Pull error: {chunk['error']}[/red]")
                        pull_error = True
                        break
            if not pull_error and total_size > 0:
                progress.update(task_id, completed=total_size, description="pulling")
        return not pull_error
    except requests.RequestException:
        raise


# ────────────────────── subprocess fallbacks ──────────────────────

def _pull_model_subprocess(model_name: str) -> None:
    """
    Download (pull) a model using subprocess.
    Parses Ollama's output and displays a clean Rich progress bar.
    """
    _console.print(f"Pulling model [bold]{model_name}[/bold]...")

    proc = None
    try:
        proc = subprocess.Popen(
            ["ollama", "pull", model_name],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True,
        )

        progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>4.0f}%"),
            TimeElapsedColumn(),
            TextColumn("<"),
            TimeRemainingColumn(),
            console=_console,
        )

        size_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB)\s*/\s*(\d+(?:\.\d+)?)\s*(KB|MB|GB)')
        unit_multipliers = {"KB": 1024, "MB": 1024**2, "GB": 1024**3}
        total_bytes = 0
        completed_bytes = 0
        last_total = 0
        last_completed = 0

        with progress:
            task_id = progress.add_task("", total=None)
            for line in proc.stdout:
                stripped = line.strip()

                match = re.search(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB)\s*/\s*(\d+(?:\.\d+)?)\s*(KB|MB|GB)', stripped)
                if match:
                    comp_val = float(match.group(1))
                    comp_unit = match.group(2)
                    total_val = float(match.group(3))
                    total_unit = match.group(4)
                    completed_bytes = comp_val * unit_multipliers.get(comp_unit, 1)
                    total_bytes = total_val * unit_multipliers.get(total_unit, 1)

                if total_bytes > 0:
                    progress.update(task_id, completed=completed_bytes, total=total_bytes, description="pulling")
                elif total_bytes == 0 and last_total == 0:
                    if "manifest" in stripped.lower() or "pulling" in stripped.lower():
                        progress.update(task_id, description="pulling manifest")
                    elif stripped:
                        progress.update(task_id, description=stripped[:80])

                last_total = total_bytes
                last_completed = completed_bytes

            proc.wait()
            if proc.returncode != 0:
                log_warning(f"`ollama pull` exited with code {proc.returncode}")

    except FileNotFoundError:
        log_warning("Ollama is not installed. Install it from https://ollama.com")
        sys.exit(1)
    except KeyboardInterrupt:
        log_warning("Download interrupted by user.")
        if proc is not None:
            proc.terminate()


def pull_model(model_name: str) -> None:
    """
    Download (pull) a model. Uses HTTP API streaming for clean progress
    bars with percentage, bar, elapsed time, and estimated time remaining.
    Falls back to subprocess if the API is unavailable.
    """
    _console.print(f"Pulling model [bold]{model_name}[/bold]...")
    _ensure_ollama()

    try:
        pull_model_stream(model_name)
    except Exception:
        _pull_model_subprocess(model_name)


def show_model_info(model_name: str) -> Optional[dict]:
    """
    Retrieve model metadata using `ollama show` (subprocess).
    Returns a JSON dict or None.
    Uses subprocess because the full show output includes modelfile content
    that the HTTP /api/show endpoint doesn't always include.
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


# ────────────────────── library search (remote) ──────────────────────

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
