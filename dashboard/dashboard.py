"""
✦ Onyx Dashboard — CLI/TUI management interface.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from rich import box
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.config import Config

console = Console()


def show_status(config: Config):
    """Show Onyx Agent status dashboard."""
    model_name = config.get("active_model", "none")
    model_cfg = config.get(f"models.{model_name}", {})

    # Status table
    table = Table(title="✦ Onyx Agent — Status", box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # Model status
    table.add_row("Model", "✅" if model_cfg.get("enabled") else "⬜",
                  f"{model_name} ({model_cfg.get('model', '?')})")

    # Messenger status
    for name, cfg in config.get("messengers", {}).items():
        icon = "✅" if cfg.get("enabled") else "⬜"
        detail = ""
        if name == "telegram":
            token = cfg.get("token", "")
            detail = f"token: {token[:8]}..." if token else "not set"
        elif name == "console":
            detail = f"prompt: {cfg.get('prompt', 'onyx> ')}"
        table.add_row(f"Messenger: {name}", icon, detail)

    # Skills status
    for name, cfg in config.get("skills", {}).items():
        icon = "✅" if cfg.get("enabled") else "⬜"
        table.add_row(f"Skill: {name}", icon, "")

    console.print(table)
    console.print()


def show_config(config: Config):
    """Show full configuration."""
    console.print(Panel(
        json.dumps(config.data, indent=2),
        title="Configuration",
        border_style="cyan",
    ))


def edit_config(config: Config):
    """Open config in default editor."""
    editor = os.environ.get("EDITOR", "nano")
    try:
        subprocess.run([editor, str(config.path)], check=True)
        config.load()
        console.print("[green]✅ Config reloaded[/]")
    except Exception as e:
        console.print(f"[red]Error opening editor: {e}[/]")


def toggle_component(config: Config, component_type: str, name: str):
    """Toggle a component (messenger, model, skill) on/off."""
    path = f"{component_type}.{name}.enabled"
    current = config.get(path, None)
    if current is None:
        console.print(f"[yellow]Unknown {component_type}: {name}[/]")
        return
    config.set(path, not current)
    console.print(f"[green]✅ {component_type}.{name} set to {not current}[/]")


def show_logs(config: Config, lines: int = 20):
    """Show recent log entries."""
    log_file = config.resolve("log_file")
    if not log_file.exists():
        console.print("[yellow]No log file found.[/]")
        return
    try:
        content = log_file.read_text().split("\n")
        recent = content[-lines:]
        for line in recent:
            if line.strip():
                console.print(line)
    except Exception as e:
        console.print(f"[red]Error reading log: {e}[/]")


def run_setup(config: Config):
    """Interactive setup wizard."""
    console.print(Panel("✦ Onyx Agent — Setup Wizard", border_style="cyan"))

    # Agent name
    current = config.get("agent_name", "Onyx")
    name = input(f"Agent name [{current}]: ").strip() or current
    config.set("agent_name", name)

    # Model selection
    console.print("\n[cyan]Available models:[/]")
    models = list(config.get("models", {}).keys())
    for i, m in enumerate(models, 1):
        status = "enabled" if config.get(f"models.{m}.enabled") else "disabled"
        console.print(f"  {i}. {m} ({status})")
    model_idx = input(f"Active model [1-{len(models)}, default: 1]: ").strip()
    if model_idx.isdigit() and 1 <= int(model_idx) <= len(models):
        selected = models[int(model_idx) - 1]
        config.set("active_model", selected)
        # Enable selected, disable others
        for m in models:
            config.set(f"models.{m}.enabled", m == selected)
        console.print(f"[green]✅ Active model: {selected}[/]")

    # Telegram setup
    console.print("\n[cyan]Telegram bot (optional):[/]")
    tg_token = input(f"Telegram bot token [{config.get('messengers.telegram.token', '')[:8]}...]: ").strip()
    if tg_token:
        config.set("messengers.telegram.token", tg_token)
        config.set("messengers.telegram.enabled", True)

    # Ollama host
    console.print("\n[cyan]Ollama (local LLM):[/]")
    ollama_host = input(f"Host [{config.get('models.ollama.host', 'http://localhost:11434')}]: ").strip()
    if ollama_host:
        config.set("models.ollama.host", ollama_host)
    ollama_model = input(f"Model [{config.get('models.ollama.model', 'gemma2:9b')}]: ").strip()
    if ollama_model:
        config.set("models.ollama.model", ollama_model)

    console.print("\n[green]✅ Setup complete![/]")
    console.print("Run [bold]onyx start[/] to launch the agent.")


def main():
    """Dashboard entry point."""
    config_path = Path("config.json") if Path("config.json").exists() else Path.cwd() / "config.json"

    if not config_path.exists():
        console.print("[yellow]No config.json found. Run setup first:[/]")
        console.print("  [bold]python onyx.py setup[/]")
        return

    config = Config(config_path)

    while True:
        console.print("\n[bold cyan]✦ Onyx Dashboard[/]")
        console.print("1. Status")
        console.print("2. View config")
        console.print("3. Edit config")
        console.print("4. Toggle messenger")
        console.print("5. Toggle skill")
        console.print("6. Toggle model")
        console.print("7. View logs")
        console.print("8. Setup wizard")
        console.print("9. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            show_status(config)
        elif choice == "2":
            show_config(config)
        elif choice == "3":
            edit_config(config)
        elif choice == "4":
            name = input("Messenger name (telegram, discord, console): ").strip()
            toggle_component(config, "messengers", name)
        elif choice == "5":
            name = input("Skill name: ").strip()
            toggle_component(config, "skills", name)
        elif choice == "6":
            name = input("Model name: ").strip()
            toggle_component(config, "models", name)
        elif choice == "7":
            show_logs(config)
        elif choice == "8":
            run_setup(config)
        elif choice == "9":
            break
        else:
            console.print("[yellow]Invalid choice[/]")


if __name__ == "__main__":
    main()
