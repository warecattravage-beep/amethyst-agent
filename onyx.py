#!/usr/bin/env python3
"""
✦ Onyx Agent — Standalone cross-platform agent gateway.

Usage:
    python onyx.py start       Launch the agent
    python onyx.py setup       Run setup wizard
    python onyx.py status      CLI dashboard
    python onyx.py dashboard   Launch GUI dashboard app
    python onyx.py config      Edit config file
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core.config import Config
from core.engine import OnyxEngine

log = logging.getLogger("onyx")


def cmd_start(args):
    """Start the Onyx Agent."""
    engine = OnyxEngine(args.config)
    try:
        asyncio.run(engine.run())
    except KeyboardInterrupt:
        log.info("Shutdown requested...")
    except Exception as e:
        log.error("Fatal error: %s", e)
        sys.exit(1)


def cmd_setup(args):
    """Run the setup wizard."""
    from dashboard.dashboard import run_setup
    config = Config(args.config)
    run_setup(config)


def cmd_status(args):
    """Show the dashboard status."""
    from dashboard.dashboard import show_status
    config = Config(args.config)
    show_status(config)


def cmd_config(args):
    """Open config in editor."""
    from dashboard.dashboard import edit_config
    config = Config(args.config)
    edit_config(config)


def cmd_logs(args):
    """Show recent logs."""
    from dashboard.dashboard import show_logs
    config = Config(args.config)
    show_logs(config, args.lines)


def _is_termux() -> bool:
    """Detect if running in Termux (Android)."""
    return bool(os.environ.get("TERMUX_VERSION")) or "/data/data/com.termux" in str(Path.cwd())


def cmd_dashboard(args):
    """Launch the dashboard — Kivy GUI on desktop, web server on Termux."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))

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


def main():
    parser = argparse.ArgumentParser(
        description="✦ Onyx Agent — Standalone AI agent gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python onyx.py setup         First-time configuration
  python onyx.py start         Launch the agent
  python onyx.py status        Dashboard overview
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
