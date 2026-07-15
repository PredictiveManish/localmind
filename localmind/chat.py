"""Interactive CLI chat with Ollama models.

This is LocalMind's answer to "how do I actually talk to my local model?"
Instead of typing `ollama run llama3` and getting a bare shell, you get:
- Streaming output (words appear as they're generated)
- Conversation history (multi-turn context)
- System prompts (set a persona)
- Parameter controls (temperature, top_k, etc.)
- Model switching mid-conversation
- Session save/load

Usage:
    lm chat llama3:8b          # Chat with a model
    lm chat llama3:8b -s "You are a helpful coding assistant"
    lm chat llama3:8b -t 0.7 -k 50 -p 0.9
"""
from __future__ import annotations
import sys
from typing import Optional, List
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.markdown import Markdown

from .ollama_api import chat as ollama_chat, _ensure_ollama_running
from .models import OllamaChatMessage, VRAMEstimate
from .vram import estimate_vram, get_best_quant, format_vram_table

console = Console()


def chat(model_name: str, system: Optional[str] = None,
         temperature: Optional[float] = None, top_k: Optional[int] = None,
         top_p: Optional[float] = None, num_ctx: Optional[int] = None,
         show_vram: bool = False) -> None:
    """
    Start an interactive chat session with an Ollama model.

    Parameters:
        model_name: e.g. "llama3:8b"
        system: optional system prompt to set model behavior
        temperature: creativity (0.0 = deterministic, 1.0 = creative)
        top_k: consider only top K tokens
        top_p: nucleus sampling probability
        num_ctx: context window size in tokens
        show_vram: show VRAM estimate before starting
    """
    # Ensure Ollama is running
    if not _ensure_ollama_running():
        console.print("[red]Ollama is not running. Start it with: ollama serve[/red]")
        sys.exit(1)

    # Show VRAM estimate if requested
    if show_vram:
        from .hardware import get_full_report
        hw = get_full_report()
        vram_gb = 0.0
        ram_gb = hw.ram.total_gb
        for gpu in hw.gpus:
            if not gpu.is_unified_memory:
                vram_gb += gpu.vram_mb / 1024.0

        estimates = estimate_vram(model_name, available_vram_gb=vram_gb,
                                  available_ram_gb=ram_gb)
        if estimates:
            console.print(Panel(f"VRAM estimate for [bold]{model_name}[/bold]:", style="blue"))
            console.print(format_vram_table(estimates, vram_gb, ram_gb))
            console.print()

    # Build options dict
    options = {}
    if temperature is not None:
        options["temperature"] = temperature
    if top_k is not None:
        options["top_k"] = top_k
    if top_p is not None:
        options["top_p"] = top_p
    if num_ctx is not None:
        options["num_ctx"] = num_ctx

    # Conversation history
    messages: List[OllamaChatMessage] = []
    if system:
        messages.append(OllamaChatMessage(role="system", content=system))

    # Welcome message
    welcome = f"""[bold blue]Chatting with {model_name}[/bold blue]

Type your message and press Enter. Send [/bold yellow]/quit[/bold yellow] to exit,
[bold yellow]/model <name>[/bold yellow] to switch models,
[bold yellow]/system <prompt>[/bold yellow] to change system prompt,
[bold yellow]/history[/bold yellow] to clear conversation,
[bold yellow]/vram[/bold yellow] to show VRAM estimates.
"""
    console.print(Panel(welcome.strip(), title="LocalMind Chat", border_style="blue"))

    # Main chat loop
    while True:
        try:
            user_input = Prompt.ask("[bold green]You[/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Goodbye![/yellow]")
            break

        # Handle commands
        if user_input.lower() in ("/quit", "/exit", "/q"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        if user_input.lower() == "/history":
            messages = [m for m in messages if m.role == "system"]
            console.print("[dim]Conversation history cleared.[/dim]")
            continue

        if user_input.lower() == "/vram":
            from .hardware import get_full_report
            hw = get_full_report()
            vram_gb = sum(g.vram_mb / 1024.0 for g in hw.gpus if not g.is_unified_memory)
            ram_gb = hw.ram.total_gb
            estimates = estimate_vram(model_name, available_vram_gb=vram_gb,
                                      available_ram_gb=ram_gb)
            if estimates:
                console.print(format_vram_table(estimates, vram_gb, ram_gb))
            continue

        if user_input.lower().startswith("/model "):
            new_model = user_input[7:].strip()
            if new_model:
                model_name = new_model
                messages = [m for m in messages if m.role == "system"]
                console.print(f"[yellow]Switched to {model_name}[/yellow]")
            continue

        if user_input.lower().startswith("/system "):
            system = user_input[8:].strip()
            messages = [m for m in messages if m.role != "system"]
            messages.insert(0, OllamaChatMessage(role="system", content=system))
            console.print(f"[yellow]System prompt set.[/yellow]")
            continue

        if not user_input:
            continue

        # Add user message
        messages.append(OllamaChatMessage(role="user", content=user_input))

        # Stream response
        console.print()
        try:
            response_parts = []
            for chunk in ollama_chat(model_name, messages, options=options, stream=True):
                if chunk:
                    response_parts.append(chunk)
                    console.print(chunk, end="", soft_wrap=True)
            console.print()  # newline after response

            # Save assistant response to history
            full_response = "".join(response_parts)
            if full_response:
                messages.append(OllamaChatMessage(role="assistant", content=full_response))

        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            # Remove the failed user message from history
            if messages and messages[-1].role == "user":
                messages.pop()
