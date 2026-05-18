"""
✦ Onyx Setup Wizard — Lightweight onboarding.
No rich/Kivy deps — works on any terminal (Linux, Windows, Termux).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _ask(label, default="", secret=False):
    """Ask for input with a visible default."""
    d = f" [{default}]" if default else ""
    prompt = f"  {label}{d}: "
    val = input(prompt).strip()
    return val if val else default


def run_setup(config) -> None:
    """Interactive setup wizard with visual onboarding flow."""
    print()
    print("  ╔═══════════════════════════════════════╗")
    print("  ║   ✦ Onyx Agent — First-Time Setup   ║")
    print("  ╚═══════════════════════════════════════╝")
    print()
    print("  Let's get your agent up and running.")
    print("  Press Enter to accept defaults in [brackets].")
    print()

    # ── Step 1: Identity ──
    print("  ─── Step 1: Identity ───")
    name = _ask("Agent name", config.get("agent_name", "Onyx"))
    config.set("agent_name", name)

    vibe = _ask("Personality (how should Onyx behave?)",
                config.get("agent_vibe", "") or "Helpful, efficient AI assistant")
    config.set("agent_vibe", vibe)
    print(f"  ✓ {name} will be: {vibe}")
    print()

    # ── Step 2: AI Model ──
    print("  ─── Step 2: AI Model ───")
    models = list(config.get("models", {}).keys())
    print("  Available backends:")
    for i, m in enumerate(models, 1):
        status = "on" if config.get(f"models.{m}.enabled") else "off"
        print(f"    {i}. {m} ({status})")
    idx = _ask("Active model", "1")
    if idx.isdigit() and 1 <= int(idx) <= len(models):
        selected = models[int(idx) - 1]
        config.set("active_model", selected)
        for m in models:
            config.set(f"models.{m}.enabled", m == selected)

    if config.get("active_model") == "ollama":
        host = _ask("Ollama host", config.get("models.ollama.host", "http://localhost:11434"))
        config.set("models.ollama.host", host)
        model = _ask("Ollama model", config.get("models.ollama.model", "gemma2:2b"))
        config.set("models.ollama.model", model)
        print("  Tip: Run 'ollama pull <model>' in another terminal if not pulled yet.")
    else:
        key = _ask("API key (sk-...)")
        if key:
            config.set(f"models.{config.get('active_model')}.api_key", key)
    print()

    # ── Step 3: Telegram Messenger ──
    print("  ─── Step 3: Messenger (optional) ───")
    print("  Onyx can chat with you through messengers.")
    current_tg = config.get("messengers.telegram.token", "")
    if current_tg:
        print(f"  Telegram token already set: {current_tg[:8]}...")
        enable = _ask("Enable Telegram?", "Y").lower()
        config.set("messengers.telegram.enabled", enable in ("y", "yes", ""))
    else:
        want_tg = _ask("Add Telegram bot?", "n").lower()
        if want_tg in ("y", "yes"):
            token = _ask("Bot token (from @BotFather)")
            if token:
                config.set("messengers.telegram.token", token)
                config.set("messengers.telegram.enabled", True)
                print("  ✓ Telegram enabled! Send /start to your bot to test.")
            else:
                print("  Skipped.")
    print()

    # ── Step 4: Proactive Mode ──
    print("  ─── Step 4: Proactive Mode ───")
    print("  Onyx can message you unprompted when idle.")
    pro = _ask("Enable proactive check-ins?", "Y").lower()
    config.set("proactive.enabled", pro in ("y", "yes", ""))
    if config.get("proactive.enabled"):
        print("  ✓ Onyx will check in ~every 30 min when idle (max 5/day)")
    else:
        print("  Onyx will only reply when you message.")
    print()

    # ── Step 5: Notion (optional) ──
    print("  ─── Step 5: Notion Integration (optional) ───")
    want_notion = _ask("Add Notion skill?", "n").lower()
    if want_notion in ("y", "yes"):
        ntoken = _ask("Notion integration token")
        if ntoken:
            config.set("notion.api_key", ntoken)
            config.set("skills.notion.enabled", True)
            print("  ✓ Notion connected!")
    print()

    # ── Summary ──
    print("  ╔═══════════════════════════════════════╗")
    print("  ║   ✅ Onyx Agent — Setup Complete!   ║")
    print("  ╚═══════════════════════════════════════╝")
    print()
    print(f"  Agent:    {config.get('agent_name')}")
    print(f"  Model:    {config.get('active_model')}")
    print(f"  Persona:  {config.get('agent_vibe', 'default')[:50]}")
    tg_on = config.get("messengers.telegram.enabled", False)
    print(f"  Telegram: {'✅ Connected' if tg_on and config.get('messengers.telegram.token') else '⬜ Not set'}")
    print(f"  Notion:   {'✅ Connected' if config.get('notion.api_key') else '⬜ Not set'}")
    pro_on = config.get("proactive.enabled", True)
    print(f"  Proactive:{' ✅ On' if pro_on else ' ⬜ Off'}")
    print()
    print("  Next steps:")
    if tg_on and config.get("messengers.telegram.token"):
        print("    1. Send /start to your bot on Telegram")
    print(f"    1. Run: onyx start     (or: python3 onyx.py start)")
    print(f"    2. Run: onyx dashboard (or: python3 onyx.py dashboard)")
    print()
    print("  Need help? Check: https://github.com/warecattravage-beep/onyx-agent-v3")
    print()
