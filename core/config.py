"""
✦ Onyx Config — Load and manage configuration.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

log = logging.getLogger("onyx.config")

DEFAULT_CONFIG: dict[str, Any] = {
    # ── Agent identity ──
    "agent_name": "Onyx",
    "agent_vibe": "Helpful, efficient AI assistant with coding skills.",

    # ── Active messenger ──
    "active_messengers": [],

    # ── Messenger configs ──
    "messengers": {
        "console": {
            "enabled": True,
            "prompt": "onyx> ",
        },
        "telegram": {
            "enabled": False,
            "token": "",
        },
        "discord": {
            "enabled": False,
            "token": "",
        },
        "signal": {
            "enabled": False,
            "cli_path": "signal-cli",
            "account": "",
        },
    },

    # ── Active model ──
    "active_model": "ollama",

    # ── Model configs ──
    "models": {
        "ollama": {
            "enabled": True,
            "host": "http://localhost:11434",
            "model": "gemma2:9b",
            "timeout": 60,
        },
        "openai": {
            "enabled": False,
            "api_key": "",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
        },
        "anthropic": {
            "enabled": False,
            "api_key": "",
            "model": "claude-sonnet-4-20250514",
        },
        "openrouter": {
            "enabled": False,
            "api_key": "",
            "model": "openrouter/auto",
        },
    },

    # ── Skills ──
    "skills": {
        "chat": {"enabled": True},
        "coding": {"enabled": True},
        "terminal": {"enabled": True},
        "web_search": {"enabled": True},
        "web_fetch": {"enabled": True},
        "file": {"enabled": True},
        "code_review": {"enabled": True},
    },

    # ── Proactive mode ──
    "proactive": {
        "enabled": True,
        "idle_minutes": 10,       # send after this many mins of silence
        "interval_minutes": 30,    # don't send again until this passes
        "quiet_hours_start": 23,   # 11 PM
        "quiet_hours_end": 8,      # 8 AM
    },

    # ── System ──
    "data_dir": "data",
    "log_file": "data/onyx.log",
    "log_level": "INFO",
}


def resolve_path(path: str | Path, base: Path | None = None) -> Path:
    """Resolve a config path relative to the config file location."""
    p = Path(path)
    if p.is_absolute():
        return p
    base = base or Path.cwd()
    return base / p


class Config:
    """Onyx Agent configuration."""

    def __init__(self, path: str | Path = "config.json"):
        self.path = Path(path)
        self.data: dict[str, Any] = {}
        self.load()

    def load(self):
        """Load config from file, merging with defaults."""
        self.data = dict(DEFAULT_CONFIG)
        if self.path.exists():
            try:
                user = json.loads(self.path.read_text())
                self._deep_merge(self.data, user)
                log.info("Config loaded from %s", self.path)
            except Exception as e:
                log.warning("Failed to load config: %s", e)
        else:
            self.save()
            log.info("Default config created at %s", self.path)

    def save(self):
        """Write config to file."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.data, indent=2))
        log.debug("Config saved to %s", self.path)

    def get(self, key: str, default=None):
        """Get a config value by dot-notation key."""
        parts = key.split(".")
        val = self.data
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
                if val is None:
                    return default
            else:
                return default
        return val

    def set(self, key: str, value: Any):
        """Set a config value by dot-notation key."""
        parts = key.split(".")
        val = self.data
        for p in parts[:-1]:
            val = val.setdefault(p, {})
        val[parts[-1]] = value
        self.save()

    def resolve(self, key: str) -> Path:
        """Resolve a path config value relative to config location."""
        raw = self.get(key, "")
        return resolve_path(raw, self.path.parent)

    def _deep_merge(self, base: dict, update: dict):
        """Recursively merge update into base."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    @property
    def active_model_config(self) -> dict:
        """Get the currently active model config."""
        name = self.data.get("active_model", "ollama")
        return self.data.get("models", {}).get(name, {})

    @property
    def active_messengers(self) -> list[str]:
        """Get list of enabled messenger names."""
        return [
            name for name, cfg in self.data.get("messengers", {}).items()
            if cfg.get("enabled")
        ]

    @property
    def enabled_skills(self) -> list[str]:
        """Get list of enabled skill names."""
        return [
            name for name, cfg in self.data.get("skills", {}).items()
            if cfg.get("enabled")
        ]
