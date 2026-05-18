"""
✦ Onyx Setup Wizard — Lightweight, no rich/Kivy dependency.
Used by install.sh and `onyx.py setup` on any platform.
"""
from __future__ import annotations

import sys
from pathlib import Path


def run_setup(config) -> None:
    """Interactive setup wizard using plain stdio (no rich)."""
    name = config.get("agent_name", "Onyx")
    print(f"\n✦ Onyx Agent — Setup Wizard")
    print(f"{'='*40}\n")

    # Agent name
    inp = input(f"Agent name [{name}]: ").strip()
    if inp:
        config.set("agent_name", inp)
        name = inp

    # Model selection
    print("\nAvailable models:")
    models = list(config.get("models", {}).keys())
    for i, m in enumerate(models, 1):
        status = "on" if config.get(f"models.{m}.enabled") else "off"
        print(f"  {i}. {m} ({status})")

    inp = input(f"Active model [1-{len(models)}, Enter=ollama]: ").strip()
    if inp.isdigit() and 1 <= int(inp) <= len(models):
        selected = models[int(inp) - 1]
        config.set("active_model", selected)
        for m in models:
            config.set(f"models.{m}.enabled", m == selected)
        print(f"  → Active model: {selected}")

    # Telegram token
    current_tg = config.get("messengers.telegram.token", "")
    masked = f"{current_tg[:8]}..." if current_tg and len(current_tg) > 8 else "(empty)"
    inp = input(f"\nTelegram bot token [{masked}]: ").strip()
    if inp:
        config.set("messengers.telegram.token", inp)
        config.set("messengers.telegram.enabled", True)
        print("  → Telegram enabled")

    # Ollama host
    default_host = config.get("models.ollama.host", "http://localhost:11434")
    inp = input(f"\nOllama host [{default_host}]: ").strip()
    if inp:
        config.set("models.ollama.host", inp)

    # Ollama model
    default_model = config.get("models.ollama.model", "gemma2:9b")
    inp = input(f"Ollama model [{default_model}]: ").strip()
    if inp:
        config.set("models.ollama.model", inp)

    # Persona
    print("\n" + "=" * 40)
    print("\nPersona — How should Onyx behave?")
    print("  Describe its personality in a few words.")
    print("  Examples:")
    print("    'Friendly coding buddy who explains everything simply'")
    print("    'Efficient sysadmin — short answers, no fluff'")
    print("    'Creative storyteller with a dark sense of humor'")
    default_vibe = config.get("agent_vibe", "")
    inp = input(f"\nPersona [{default_vibe or 'Helpful, efficient AI assistant'}]: ").strip()
    if inp:
        config.set("agent_vibe", inp)
    elif not default_vibe:
        config.set("agent_vibe", "Helpful, efficient AI assistant")

    # Proactive mode
    print("\n" + "=" * 40)
    pro = config.get("proactive", {}).get("enabled", True)
    inp = input(f"\nProactive mode — let Onyx message you unprompted? [Y/n]: ").strip().lower()
    config.set("proactive.enabled", inp not in ("n", "no"))

    print(f"\n{'='*40}")
    print(f"✅ Setup complete!")
    print(f"   Agent: {config.get('agent_name')}")
    print(f"   Model: {config.get('active_model')}")
    print(f"\nNext steps:")
    print(f"   python3 onyx.py start     — Launch agent")
    print(f"   python3 onyx.py dashboard — Open dashboard")
    print()
