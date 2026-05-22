#!/usr/bin/env python3
"""
* Amethyst Agent - Standalone cross-platform agent gateway.

Usage:
    python amethyst.py start       Launch the agent
    python amethyst.py setup       Run setup wizard
    python amethyst.py status      CLI dashboard
    python amethyst.py dashboard   Launch GUI dashboard app
    python amethyst.py config      Edit config file
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# ── Find project root ──
# The script may be symlinked or copied (e.g. $PREFIX/bin/amethyst).
# Search for the actual project directory containing core/
_script = Path(__file__).resolve()
ROOT = _script.parent
# If we're in a system bin dir, look for the project in home
if not (ROOT / "core").is_dir():
    for candidate in [
        Path.home() / "amethyst-agent-v3",
        Path.home() / "amethyst",
        _script.parent.parent / "amethyst-agent-v3",
    ]:
        if (candidate / "core").is_dir():
            ROOT = candidate
            break
sys.path.insert(0, str(ROOT))

log = logging.getLogger("amethyst")


# ── Platform detection ──

def _is_termux() -> bool:
    """Detect if running in Termux (Android)."""
    return bool(os.environ.get("TERMUX_VERSION")) or "/data/data/com.termux" in str(Path.cwd())


# ── Commands ──

def cmd_start(args):
    """Start the Amethyst Agent."""
    from core.config import Config
    from core.engine import AmethystEngine
    engine = AmethystEngine(args.config)

    # Print dashboard URL before entering run loop
    print()
    print("  ✦ Amethyst Agent running")
    print(f"  Dashboard: http://localhost:9091")
    print("  (run `python amethyst.py dashboard` to open)")
    print()

    try:
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        log.info("Shutdown requested...")
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)


def cmd_setup(args):
    """Run the setup wizard."""
    from core.config import Config
    from core.setup_wizard import run_setup
    config = Config(args.config)
    run_setup(config)


def cmd_status(args):
    """Show the dashboard status."""
    from core.config import Config
    from dashboard.dashboard import show_status
    config = Config(args.config)
    show_status(config)


def cmd_config(args):
    """Open config in editor."""
    from core.config import Config
    from dashboard.dashboard import edit_config
    config = Config(args.config)
    edit_config(config)


def cmd_logs(args):
    """Show recent logs."""
    from core.config import Config
    from dashboard.dashboard import show_logs
    config = Config(args.config)
    show_logs(config, args.lines)


def cmd_dashboard(args):
    """Launch the dashboard - Kivy GUI on desktop, web server on Termux."""
    if _is_termux() or args.web:
        from dashboard.web_dashboard import run as web_run
        web_run(args.config)
    else:
        try:
            from dashboard.app import main as gui_main
            gui_main()
        except ImportError:
            print("Kivy not installed. Launching web dashboard instead...")
            from dashboard.web_dashboard import run as web_run
            web_run(args.config)


def cmd_help():
    print(__doc__.strip())


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="* Amethyst Agent - Standalone AI agent gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python amethyst.py setup         First-time configuration
  python amethyst.py start         Launch the agent
  python amethyst.py status        Dashboard overview
        """,
    )
    parser.add_argument(
        "--config", "-c",
        default="config.json",
        help="Path to config file (default: config.json)",
    )
    parser.add_argument(
        "--lines", "-l",
        type=int, default=20,
        help="Number of log lines (default: 20)",
    )
    parser.add_argument(
        "--web", "-w",
        action="store_true",
        help="Force web dashboard mode (instead of Kivy GUI)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["start", "setup", "status", "config", "logs", "dashboard", "help"],
        help="Command to run",
    )

    args = parser.parse_args()

    commands = {
        "start": cmd_start,
        "setup": cmd_setup,
        "status": cmd_status,
        "config": cmd_config,
        "logs": cmd_logs,
        "dashboard": cmd_dashboard,
        "help": lambda a: print(parser.format_help()),
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
