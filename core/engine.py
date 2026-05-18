"""
✦ Onyx Engine — Core message router and lifecycle manager.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


# ── ANSI Colors ──

class C:
    """Terminal colors (ANSI). Falls back to empty strings if not supported."""
    _support = True
    try:
        if not sys.stdout.isatty():
            _support = False
    except Exception:
        _support = False

    VIOLET = "\033[38;5;141m" if _support else ""
    CYAN = "\033[38;5;51m" if _support else ""
    GREEN = "\033[38;5;83m" if _support else ""
    YELLOW = "\033[38;5;227m" if _support else ""
    RED = "\033[38;5;196m" if _support else ""
    DIM = "\033[38;5;240m" if _support else ""
    BOLD = "\033[1m" if _support else ""
    NC = "\033[0m" if _support else ""

from core.config import Config
from core.memory import Memory
from core.messenger import Messenger, MessageHandler

# ── Messenger imports ──
from messengers.console import ConsoleMessenger
from messengers.telegram_messenger import TelegramMessenger
from messengers.discord_messenger import DiscordMessenger
from messengers.signal_messenger import SignalMessenger

# ── Model imports ──
from models.ollama_model import OllamaModel
from models.openai_model import OpenAIModel

# ── Skill imports ──
from skills.chat import ChatSkill
from skills.coding import CodingSkill
from skills.terminal import TerminalSkill
from skills.web_search import WebSearchSkill
from skills.web_fetch import WebFetchSkill
from skills.file_skill import FileSkill
from skills.code_review import CodeReviewSkill

log = logging.getLogger("onyx.engine")

MESSENGER_MAP = {
    "console": ConsoleMessenger,
    "telegram": TelegramMessenger,
    "discord": DiscordMessenger,
    "signal": SignalMessenger,
}

MODEL_MAP = {
    "ollama": OllamaModel,
    "openai": OpenAIModel,
    "anthropic": None,  # TODO
    "openrouter": None,  # maps to OpenAIModel with custom base_url
}

SKILL_MAP = {
    "chat": ChatSkill,
    "coding": CodingSkill,
    "terminal": TerminalSkill,
    "web_search": WebSearchSkill,
    "web_fetch": WebFetchSkill,
    "file": FileSkill,
    "code_review": CodeReviewSkill,
}


class OnyxEngine:
    """Main engine — routes messages, manages lifecycle."""

    def __init__(self, config_path: str | Path = "config.json"):
        self.config = Config(config_path)
        self.messengers: dict[str, Messenger] = {}
        self.model = None
        self.skills: dict[str, Any] = {}
        self._running = False
        self._console: ConsoleMessenger | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self._start_time = datetime.now(timezone.utc)
        self._memory = Memory(self.config.resolve("data_dir") / "memory.json")
        self._last_msg_time = time.time()

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        level = getattr(logging, self.config.get("log_level", "INFO"), logging.INFO)
        log_dir = Path(self.config.get("data_dir", "data"))
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.config.resolve("log_file")

        # Colored log formatter
        class ColorFormatter(logging.Formatter):
            LVL_COLORS = {
                "DEBUG": C.DIM,
                "INFO": C.CYAN,
                "WARNING": C.YELLOW,
                "ERROR": C.RED,
                "CRITICAL": C.RED + C.BOLD,
            }
            LVL_SHORT = {
                "DEBUG": "DBG",
                "INFO": "INF",
                "WARNING": "WRN",
                "ERROR": "ERR",
                "CRITICAL": "CRT",
            }
            NAME_COLORS = {
                "onyx": "",
                "onyx.engine": C.VIOLET,
                "onyx.ollama": C.CYAN,
                "onyx.telegram": C.GREEN,
                "onyx.skill": C.YELLOW,
                "onyx.memory": C.DIM,
            }

            def format(self, record):
                # Short level
                short = self.LVL_SHORT.get(record.levelname, record.levelname[:3])
                color = self.LVL_COLORS.get(record.levelname, "")
                record.levelname = f"{color}{short}{C.NC}"
                # Short module name
                name = record.name
                nc = self.NAME_COLORS.get(name, C.DIM)
                record.name = f"{nc}{name.split('.')[-1][:6]:>6s}{C.NC}"
                # Short time (HH:MM only)
                from datetime import datetime
                ts = datetime.fromtimestamp(record.created).strftime("%H:%M")
                record.asctime = ts
                msg = super().format(record)
                return msg

        handler = logging.StreamHandler()
        handler.setFormatter(ColorFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
        handlers = [handler]
        try:
            fh = logging.FileHandler(str(log_file))
            fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
            handlers.append(fh)
        except Exception:
            pass

        logging.basicConfig(level=level, handlers=handlers)

    # ── ASCII Banner ──

    def _print_banner(self):
        """Print the gateway ASCII art banner (no counts — just the art)."""
        name = self.config.get("agent_name", "Onyx")
        v = C.VIOLET; nc = C.NC; b = C.BOLD
        print()
        print(f"{v}    ██████╗  ███╗  ██╗ ██╗  ██╗ ██╗  ██╗{nc}")
        print(f"{v}   ██╔═══██╗ ████╗ ██║ ╚██╗ ██╔╝ ╚██╗██╔╝{nc}")
        print(f"{v}   ██║   ██║ ██╔██╗██║  ╚████╔╝   ╚███╔╝{nc}")
        print(f"{v}   ██║   ██║ ██║╚████║   ╚██╔╝    ██╔██╗{nc}")
        print(f"{v}   ╚██████╔╝ ██║ ╚███║    ██║    ██╔╝ ██╗{nc}")
        print(f"{v}    ╚═════╝  ╚═╝  ╚══╝    ╚═╝    ╚═╝  ╚═╝{nc}")
        print()
        print(f"{b}       ✦ {name} Agent Gateway ✦{nc}")
        print()

    def _print_status_line(self):
        """Print a compact status line after initialization."""
        m = self.config.get("active_model", "?").upper()
        nv = C.VIOLET; nc = C.NC
        print(f"{nv}  Model: {m}  |  {len(self.skills)} Skills  |  {len(self.messengers)} Messengers{nc}")
        print()

    # ── Initialization ──

    async def init_models(self):
        """Initialize the active AI model."""
        model_name = self.config.get("active_model", "ollama")
        model_cfg = self.config.get(f"models.{model_name}", {})

        if not model_cfg.get("enabled"):
            log.warning("Active model '%s' is disabled in config", model_name)
            return

        cls = MODEL_MAP.get(model_name)
        if cls is None:
            # Try openrouter as openai
            if model_name == "openrouter":
                model_cfg["base_url"] = "https://openrouter.ai/api/v1"
                from models.openai_model import OpenAIModel
                cls = OpenAIModel

        if cls is None:
            log.warning("Unknown model: %s", model_name)
            return

        self.model = cls(model_cfg)
        if hasattr(self.model, "start"):
            await self.model.start()
        log.info("Model initialized: %s", model_name)

    async def init_messengers(self):
        """Initialize all enabled messengers."""
        for name, cfg in self.config.get("messengers", {}).items():
            if not cfg.get("enabled"):
                continue
            cls = MESSENGER_MAP.get(name)
            if cls is None:
                log.warning("Unknown messenger: %s", name)
                continue
            messenger = cls(cfg)
            messenger.on_message(self._on_message)
            await messenger.start()
            self.messengers[name] = messenger
            if isinstance(messenger, ConsoleMessenger):
                self._console = messenger

    async def init_skills(self):
        """Initialize all enabled skills."""
        for name, cfg in self.config.get("skills", {}).items():
            if not cfg.get("enabled"):
                continue
            cls = SKILL_MAP.get(name)
            if cls is None:
                log.warning("Unknown skill: %s", name)
                continue
            self.skills[name] = cls(cfg)
        log.info("Skills loaded: %s", ", ".join(self.skills.keys()))

    # ── Message handling ──

    async def _on_message(self, text: str, meta: dict[str, Any]):
        """Handle an incoming message from any messenger."""
        await self._message_queue.put((text, meta))

    async def _process_message(self, text: str, meta: dict[str, Any]):
        """Process a single message through the model and skills."""
        source = meta.get("source", "unknown")
        chat_id = meta.get("chat_id", "")
        sender = meta.get("sender", "?")

        log.info("Message from %s (%s): %.50s", sender, source, text)

        # Handle internal commands
        if text.startswith("/"):
            response = await self._handle_command(text, meta)
            if response:
                await self._send(chat_id, response, source)
            return

        # Track activity time
        self._last_msg_time = time.time()

        # Store user message in memory
        self._memory.add(chat_id, "user", text)

        # Show typing indicator (Telegram) before model call
        await self._send_action(chat_id, source)

        # Build conversation context
        messages = self._build_messages(text, meta)

        # Get model response
        if not self.model:
            await self._send(chat_id, "Error: No AI model configured.", source)
            return

        response = await self.model.chat(messages)

        # Store assistant response in memory
        self._memory.add(chat_id, "assistant", response)

        # Check if response contains skill invocations
        response = await self._process_skill_calls(response)

        # Send response
        await self._send(chat_id, response, source)

    def _build_messages(self, text: str, meta: dict) -> list[dict]:
        """Build the message list for the model."""
        chat_id = meta.get("chat_id", "")
        skills_list = list(self.skills.keys())
        vibe = self.config.get("agent_vibe", "Helpful, efficient AI assistant")
        system = self.model.system_prompt(skills_list, self.config.get("agent_name", "Onyx"))
        messages = [{"role": "system", "content": f"{system}\n\nPersonality: {vibe}"}]
        # Include recent conversation history
        history = self._memory.get_context(chat_id, max_msgs=10)
        messages.extend(history)
        # Add current user message
        messages.append({"role": "user", "content": text})
        return messages

    async def _process_skill_calls(self, response: str) -> str:
        """Parse and execute skill calls from the model response.

        Format: @skill_name(key=value, key2=value2)
        """
        import re
        pattern = r'@(\w+)\(([^)]*)\)'

        def parse_kwargs(text: str) -> dict:
            kwargs = {}
            for pair in text.split(","):
                pair = pair.strip()
                if "=" in pair:
                    k, v = pair.split("=", 1)
                    kwargs[k.strip()] = v.strip().strip("\"'")
            return kwargs

        def replace_skill(match):
            skill_name = match.group(1)
            kwargs_str = match.group(2)

            if skill_name not in self.skills:
                return f"*Unknown skill: {skill_name}*"

            kwargs = parse_kwargs(kwargs_str)
            skill = self.skills[skill_name]

            try:
                loop = asyncio.get_event_loop()
                future = asyncio.ensure_future(skill.run({"response": response}, **kwargs))
                result = loop.run_until_complete(future)
                return result or "(done)"
            except Exception as e:
                return f"*Skill error: {e}*"

        result = re.sub(pattern, replace_skill, response)
        return result

    async def _handle_command(self, text: str, meta: dict) -> str | None:
        """Handle internal commands (/help, /status, etc)."""
        cmd = text.lower().split()[0]
        chat_id = meta.get("chat_id", "")
        source = meta.get("source", "")

        if cmd == "/help":
            return self._format_help()
        elif cmd == "/status":
            return self._format_status()
        elif cmd == "/models":
            return self._format_models()
        elif cmd == "/skills":
            return self._format_skills()
        elif cmd == "/clear":
            self._memory.clear(chat_id)
            self._memory._dirty = True
            self._memory.save()
            return "🧹 Memory cleared."
        elif cmd == "/update":
            return await self._handle_update()
        elif cmd == "/config":
            return "Use the config file: config.json"
        return None

    def _format_help(self) -> str:
        lines = [
            f"**✦ {self.config.get('agent_name', 'Onyx')} Agent**",
            "",
            "**Commands:**",
            "/help — This message",
            "/status — System status",
            "/models — Available AI models",
            "/skills — Enabled skills",
            "/clear — Clear conversation memory",
            "/update — Pull latest code and update dependencies",
            "/config — Configuration info",
            "",
            "**Skills available:**",
        ]
        for name, skill in self.skills.items():
            lines.append(f"  • **{name}** — {skill.description[:60]}")
        lines.extend([
            "",
            "**Usage:**",
            "Type naturally to chat. Use `@skill_name(key=value)` in responses.",
            "Example: `@terminal(command='ls -la')`",
        ])
        return "\n".join(lines)

    def _format_status(self) -> str:
        uptime = datetime.now(timezone.utc) - self._start_time
        hours = int(uptime.total_seconds() // 3600)
        mins = int((uptime.total_seconds() % 3600) // 60)
        model_name = self.config.get("active_model", "none")
        return (
            f"**✦ {self.config.get('agent_name', 'Onyx')} Status**\n\n"
            f"⏱ Uptime: {hours}h {mins}m\n"
            f"🧠 Model: {model_name}\n"
            f"💬 Messengers: {', '.join(self.messengers.keys()) or 'none'}\n"
            f"🔧 Skills: {len(self.skills)} active\n"
        )

    def _format_models(self) -> str:
        lines = ["**Available Models:**", ""]
        for name, cfg in self.config.get("models", {}).items():
            if cfg.get("enabled"):
                model_name = cfg.get("model", name)
                active = "← active" if name == self.config.get("active_model") else ""
                lines.append(f"  • **{name}** — {model_name} {active}")
        return "\n".join(lines)

    def _format_skills(self) -> str:
        lines = ["**Enabled Skills:**", ""]
        for name, skill in self.skills.items():
            lines.append(f"  • **{name}** — {skill.description[:60]}")
        return "\n".join(lines)

    async def _handle_update(self) -> str:
        """Run git pull and update dependencies."""
        import shutil

        git_path = shutil.which("git")
        if not git_path:
            return "❌ Git is not available on this system."

        try:
            proc = await asyncio.create_subprocess_exec(
                git_path, "pull",
                cwd=Path(__file__).parent.parent,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
            pull_output = stdout.decode().strip()
            if stderr.decode().strip():
                pull_output += "\n" + stderr.decode().strip()

            # Update dependencies
            pip_proc = await asyncio.create_subprocess_exec(
                shutil.which("pip3") or "pip", "install", "-r", "requirements.txt",
                cwd=Path(__file__).parent.parent,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            pip_stdout, pip_stderr = await asyncio.wait_for(pip_proc.communicate(), timeout=120)
            pip_output = pip_stdout.decode().strip()
            if pip_stderr.decode().strip():
                pip_output += "\n" + pip_stderr.decode().strip()

            result = f"**Git pull:**\n```\n{pull_output}\n```"
            if pip_output:
                result += f"\n**Dependencies:**\n```\n{pip_output}\n```"
            return result
        except asyncio.TimeoutError:
            return "❌ Update timed out."
        except Exception as e:
            return f"❌ Update failed: {e}"

    async def _send(self, target: str, text: str, source: str):
        """Send a response back through the appropriate messenger."""
        if source == "telegram":
            tg = self.messengers.get("telegram")
            if tg:
                await tg.send(target, text)
        elif source == "discord":
            dc = self.messengers.get("discord")
            if dc:
                await dc.send(target, text)
        elif source == "console":
            console = self.messengers.get("console")
            if console:
                await console.send(target, text)

    async def _send_action(self, target: str, source: str):
        """Send a typing indicator before processing."""
        if source == "telegram":
            tg = self.messengers.get("telegram")
            if tg and hasattr(tg, "send_action"):
                await tg.send_action(target)

    # ── Main loop ──

    async def run(self):
        """Start the engine and all components."""
        self._running = True
        self._start_time = datetime.now(timezone.utc)

        self._print_banner()
        log.info("✦ Loading...")
        await self.init_skills()
        await self.init_models()
        await self.init_messengers()

        log.info("✦ Ready — %d skills, %d messengers",
                 len(self.skills), len(self.messengers))
        self._print_status_line()

        # Console input loop
        if self._console:
            asyncio.create_task(self._console_loop())

        # Telegram polling loop
        tg = self.messengers.get("telegram")
        if tg and hasattr(tg, "poll"):
            asyncio.create_task(self._telegram_poll_loop(tg))

        # Proactive check-in loop
        asyncio.create_task(self._proactive_loop())

        # Auto-update loop (check every 30 min)
        asyncio.create_task(self._auto_update_loop())

        # Main message processing loop
        await self._message_loop()

    async def _console_loop(self):
        """Read console input and queue messages."""
        while self._running and self._console:
            text = await self._console.read_input()
            if text is None:
                self._running = False
                break
            if text.lower() == "/quit":
                self._running = False
                break
            await self._message_queue.put((text, {
                "source": "console",
                "chat_id": "local",
                "sender": "you",
            }))

    async def _telegram_poll_loop(self, tg: TelegramMessenger):
        """Poll Telegram for updates."""
        while self._running:
            await tg.poll()
            await asyncio.sleep(1)

    async def _proactive_loop(self):
        """Send proactive messages when idle — random timing, guaranteed min 1/30min."""
        pro = self.config.get("proactive", {})
        if not pro.get("enabled", True):
            return
        idle_min = pro.get("idle_minutes", 10)
        interval_min = pro.get("interval_minutes", 30)
        quiet_start = pro.get("quiet_hours_start", 23)
        quiet_end = pro.get("quiet_hours_end", 8)
        force_after = interval_min * 60
        last_sent = 0
        import random

        # Daily counter
        _date = ""
        _day_count = 0

        while self._running:
            await asyncio.sleep(60)
            now = time.time()

            # Reset daily counter at midnight
            today = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")
            if today != _date:
                _date = today
                _day_count = 0

            # Skip if not idle enough
            if now - self._last_msg_time < idle_min * 60:
                continue

            # Skip if within quiet hours
            tz_kst = timezone(timedelta(hours=9))
            hour = datetime.now(tz_kst).hour
            if quiet_end < hour < quiet_start:
                continue

            # Skip if sent too recently
            elapsed = now - last_sent
            if elapsed < force_after:
                continue

            # Random: sometimes send early, but FORCE after interval_min
            # If elapsed > interval_min * 1.2: force send (guaranteed minimum)
            # Otherwise: 30% random chance per check
            if elapsed < force_after * 1.2 and random.random() > 0.3:
                continue

            # Daily limit check
            max_day = pro.get("max_per_day", 15)
            if _day_count >= max_day:
                continue

            # Send proactive message
            tg = self.messengers.get("telegram")
            if not tg or not tg.is_running:
                continue

            prompts = [
                "Hey, everything running smoothly. Anything on your mind?",
                "System's quiet. Just checking in — need anything?",
                "Been a while since we chatted. All good?",
                "I'm here if you need me. Just say the word.",
            ]
            msg = random.choice(prompts)
            last_sent = now
            _day_count += 1
            log.info("Proactive: %s (%d/%d)", msg, _day_count, max_day)
            for chat_id in ["8601374613"]:
                await tg.send(chat_id, msg)

    async def _message_loop(self):
        """Process messages from the queue."""
        while self._running:
            try:
                text, meta = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )
                await self._process_message(text, meta)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                log.error("Message processing error: %s", e)

        await self._shutdown()

    async def _auto_update_loop(self):
        """Auto-update from GitHub every 30 min."""
        import subprocess
        repo = Path(__file__).resolve().parent.parent
        while self._running:
            await asyncio.sleep(1800)
            try:
                r = subprocess.run(
                    ["git", "pull"], capture_output=True, text=True, timeout=30,
                    cwd=str(repo),
                )
                if r.returncode == 0 and r.stdout.strip():
                    if "Already up to date." not in r.stdout:
                        log.info("Auto-update: new changes pulled!")
                        # Notify all messengers
                        for m in self.messengers.values():
                            try:
                                await m.send("", "🔄 Onyx auto-updated — restarting...")
                            except Exception:
                                pass
                        log.info("Auto-update: restarting...")
                        self._running = False
                        # Replace process with fresh start
                        os.execv(sys.executable, [sys.executable, str(repo / "onyx.py"), "start"])
            except Exception as e:
                log.debug("Auto-update check failed: %s", e)

    async def _shutdown(self):
        """Gracefully shut down all components."""
        log.info("✦ Onyx Agent shutting down...")
        self._memory.save()
        for messenger in self.messengers.values():
            await messenger.stop()
        if self.model and hasattr(self.model, "stop"):
            await self.model.stop()
        log.info("✦ Onyx Agent stopped.")
