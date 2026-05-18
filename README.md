# ✦ Onyx Agent Gateway

> **Your own personal AI agent gateway — runs entirely on your machine.**
> Connect multiple messengers, switch between AI models, and enable plugin skills — all from one local app with a native dashboard.

```
     ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗
    ██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝
    ██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝
    ██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗
    ╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗
     ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝
            ✦ Agent Gateway ✦
```

---

## 📋 Table of Contents

- [What is this?](#-what-is-this)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Commands](#-commands)
- [Messengers](#-messengers)
- [Models](#-models)
- [Skills](#-skills)
- [Dashboards](#-dashboards)
- [Architecture](#-architecture)
- [Installation per Platform](#-installation-per-platform)
- [Configuration](#-configuration)
- [Roadmap](#-roadmap)
- [License](#-license)

---

## 🤔 What is this?

**Onyx Agent Gateway** is a **standalone AI agent** that you run on your own machine (no cloud dependency).

Think of it as your own private **OpenClaw** — it can:
- 💬 Chat with you through **Telegram, Discord, or your terminal**
- 🧠 Use **different AI models** — local (Ollama) or cloud (OpenAI, Claude)
- 🔧 Execute **plugin skills** — write code, run terminal commands, search the web
- 🖥️ Be managed through a **native GUI dashboard** or **web UI**

Everything is **offline-first**, configurable through a dashboard, and runs on **Windows, Linux, and Android (Termux)**.

---

## ✨ Features

### 💬 Multi-Messenger
| Messenger | Status | How to use |
|---|---|---|
| 📟 **Console** | ✅ Ready | Local terminal — no setup needed |
| ✈️ **Telegram** | ✅ Ready | Create a bot with BotFather, paste the token |
| 🎮 **Discord** | 🟡 Beta | Bot token + channel ID |
| 📱 **Signal** | 🔜 Coming | |
| 💚 **WhatsApp** | 🔜 Coming | |

### 🧠 Multi-Model
| Model | Type | How to use |
|---|---|---|
| 🦙 **Ollama** (local) | ✅ Ready | Run `ollama pull gemma2:9b` — free, private |
| 🤖 **OpenAI** (GPT-4o) | ✅ Ready | Paste your API key in config |
| 🟣 **Claude** (Anthropic) | 🔜 Coming | |
| 🔀 **OpenRouter** | 🟡 Beta | Use with OpenAI backend |

### 🔧 Plugin Skills
| Skill | What it does | Example |
|---|---|---|
| 💬 **chat** | General conversation | Always active |
| 💻 **coding** | Write + run Python, bash, Node.js | `Write a script to monitor CPU temp` |
| 🖥️ **terminal** | Run shell commands (safe blocklist) | `Show disk usage` |
| 🌐 **web_search** | Search Brave or DuckDuckGo | `What's the latest AI news?` |
| 📄 **web_fetch** | Fetch and extract any URL | `Get the content of that page` |

### 🖥️ Cross-Platform Dashboards
| Platform | Dashboard Type | How to launch |
|---|---|---|
| 🐧 **Linux** | Kivy Native GUI | `python3 onyx.py dashboard` |
| 🪟 **Windows** | Kivy Native GUI | `python3 onyx.py dashboard` |
| 📱 **Android (Termux)** | 🌐 Web Dashboard | `python3 onyx.py dashboard` → `localhost:9091` |
| 🌐 **Any (no Kivy)** | 🌐 Web Dashboard | `python3 onyx.py dashboard --web` |

---

## 🚀 Quick Start

### 1️⃣ Install

```bash
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
```

The installer will:
- ✅ Detect your platform (Linux / Windows / Termux)
- ✅ Install the right dependencies automatically
- ✅ Create a default `config.json`
- ✅ Make `onyx.py` executable
- ✅ Ask if you want to run the setup wizard

### 2️⃣ Setup

```bash
python3 onyx.py setup
```

The wizard will walk you through:
- ✏️ Agent name
- 🧠 Active AI model (Ollama, OpenAI)
- ✈️ Telegram bot token (optional)
- 🦙 Ollama host + model name

### 3️⃣ Launch

```bash
# Chat with the agent in your terminal:
python3 onyx.py start

# Or open the dashboard in another terminal:
python3 onyx.py dashboard
```

---

## 📟 Commands

| Command | What it does |
|---|---|
| `python3 onyx.py setup` | 🎯 First-time configuration wizard |
| `python3 onyx.py start` | ▶️ Launch the agent gateway |
| `python3 onyx.py dashboard` | 🖥️ Open GUI dashboard (Kivy or Web) |
| `python3 onyx.py dashboard --web` | 🌐 Force web dashboard mode |
| `python3 onyx.py status` | 📊 CLI status overview |
| `python3 onyx.py config` | 📝 Edit config.json |
| `python3 onyx.py logs` | 📋 View recent logs |
| `python3 onyx.py --help` | ❓ Show all commands |

### Agent Commands (while running)

Inside the agent, type:
- `/help` — Show available commands
- `/status` — System status
- `/models` — List and switch AI models
- `/skills` — Show enabled skills
- `/quit` — Exit the agent

---

## ✈️ Messengers

Toggle messengers on/off from the dashboard (Messengers tab) or directly in `config.json`:

```json
"messengers": {
  "console": {
    "enabled": true,
    "prompt": "onyx> "
  },
  "telegram": {
    "enabled": true,
    "token": "7865432:AAHd8s9a..."
  },
  "discord": {
    "enabled": false,
    "token": ""
  },
  "signal": {
    "enabled": false,
    "cli_path": "signal-cli",
    "account": ""
  }
}
```

> **Telegram setup:** Create a bot via [@BotFather](https://t.me/BotFather), get the token, paste it in the config.

---

## 🧠 Models

Switch between AI backends from the dashboard (Models tab) or `config.json`:

```json
"models": {
  "ollama": {
    "enabled": true,
    "host": "http://localhost:11434",
    "model": "gemma2:9b"
  },
  "openai": {
    "enabled": false,
    "api_key": "sk-...",
    "model": "gpt-4o"
  }
}
```

- **Ollama** — Free, private, runs locally. Supports Gemma, Llama, Mistral, etc.
- **OpenAI** — Cloud-based GPT models. Requires an API key.
- Switch anytime with `/models` in the agent or tap "Use" on the dashboard.

---

## 🔧 Skills

Skills are the agent's **abilities**. Enable/disable them from the dashboard or `config.json`:

| Skill | Default | Description |
|---|---|---|
| 💬 `chat` | ✅ On | General conversation and Q&A. Always available. |
| 💻 `coding` | ✅ On | Write and execute Python, bash, and Node.js scripts in a sandboxed temp directory. |
| 🖥️ `terminal` | ✅ On | Run shell commands. Includes a safety blocklist (`sudo`, `rm -rf /`, etc.). |
| 🌐 `web_search` | ✅ On | Search the web via DuckDuckGo (free) or Brave API (with key). |
| 📄 `web_fetch` | ✅ On | Fetch any URL and extract readable text content. |

### How skills work

When the AI model wants to use a skill, it formats a command like:

```
@coding(code='print("hello")', language='py')
@terminal(command='ls -la /tmp')
@web_search(query='latest AI news 2026')
@web_fetch(url='https://example.com')
```

The engine parses these, executes the skill, and returns the result to the AI.

---

## 🖥️ Dashboards

### 🐧 / 🪟 Desktop (Kivy GUI)

The native GUI dashboard has **6 tabs**:

| Tab | What you can do |
|---|---|
| 📊 **Status** | See model, messengers, skills at a glance |
| ✈️ **Messengers** | Toggle Telegram/Discord/Console on/off |
| 🧠 **Models** | Pick active model, toggle backends |
| 🔧 **Skills** | Enable/disable coding, terminal, web search |
| 📝 **Config** | Edit raw JSON, save & reload |
| 📋 **Logs** | View last 40 log lines, refresh |

### 📱 Android / Termux (Web Dashboard)

When running on Termux, the dashboard launches as a **local web server** at **`http://localhost:9091`**.

Same features as the GUI — all in your browser:
- Toggle messengers with switches
- Switch AI models with one tap
- Enable/disable skills
- Edit config in-browser
- View live logs

---

## 🏗️ Architecture

```
📁 onyx-agent/
├── 📄 onyx.py              🚪 Entry point — CLI commands
├── 📄 config.json          ⚙️ User configuration (auto-created)
├── 📄 install.sh           📦 Cross-platform installer
├── 📄 requirements.txt     📋 Python dependencies
│
├── 📁 core/                🧠 Engine layer
│   ├── 📄 config.py        Config load/save with dot-notation
│   ├── 📄 engine.py        Main router — messages → model → skills
│   ├── 📄 messenger.py     🔌 Base messenger interface
│   ├── 📄 model.py         🔌 Base AI model interface
│   └── 📄 skill.py         🔌 Base skill interface
│
├── 📁 messengers/          💬 Chat channels
│   ├── 📄 console.py       Local terminal
│   ├── 📄 telegram_messenger.py  Telegram bot (HTTP polling)
│   └── 📄 discord_messenger.py   Discord bot (HTTP API)
│
├── 📁 models/              🧠 AI backends
│   ├── 📄 ollama_model.py  Local LLM via Ollama
│   └── 📄 openai_model.py  OpenAI / OpenRouter API
│
├── 📁 skills/              🔧 Plugin abilities
│   ├── 📄 chat.py          General conversation
│   ├── 📄 coding.py        Code execution sandbox
│   ├── 📄 terminal.py      Shell commands (safe)
│   ├── 📄 web_search.py    Brave / DuckDuckGo
│   └── 📄 web_fetch.py     URL content extraction
│
└── 📁 dashboard/           🖥️ User interfaces
    ├── 📄 app.py           Kivy native GUI (desktop)
    ├── 📄 web_dashboard.py Web UI (Termux/fallback)
    └── 📄 dashboard.py     CLI text-based dashboard
```

### Data Flow

```
User (Telegram/Discord/Console)
        │
        ▼
   OnyxEngine (router)
        │
        ├── Command? ──→ /help, /status, /models
        │
        └── Message? ──→ AI Model ──→ Skill call? ──→ Execute ──→ Return
                                │
                                └── Text response ──→ Messenger ──→ User
```

---

## 📦 Installation per Platform

### 🐧 Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip git
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
```

### 🪟 Windows

1. Install [Python 3.10+](https://python.org)
2. Open PowerShell / CMD
3. ```powershell
   git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
   cd onyx-agent-v3
   pip install kivy httpx
   python onyx.py setup
   python onyx.py dashboard
   ```

### 📱 Android (Termux)

```bash
pkg update && pkg upgrade
pkg install python git
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
python3 onyx.py setup
python3 onyx.py dashboard
# Open http://localhost:9091 in your browser
```

---

## ⚙️ Configuration

All settings live in `config.json`. You can also edit it from the dashboard.

### Basic settings

| Key | Default | Description |
|---|---|---|
| `agent_name` | `Onyx` | The agent's name |
| `active_model` | `ollama` | Which model backend to use |
| `active_messengers` | `["console"]` | Which messengers are active |

### Model settings

| Key | Description |
|---|---|
| `models.ollama.host` | Ollama server URL (default: `http://localhost:11434`) |
| `models.ollama.model` | Model name (default: `gemma2:9b`) |
| `models.openai.api_key` | Your OpenAI API key |
| `models.openai.model` | Model name (default: `gpt-4o`) |

### Logging

| Key | Default | Description |
|---|---|---|
| `log_file` | `data/onyx.log` | Log file path |
| `log_level` | `INFO` | Log level (DEBUG, INFO, WARNING) |

---

## 🗺️ Roadmap

- [x] ✅ Console messenger
- [x] ✅ Telegram bot messenger
- [ ] 🔜 Discord full gateway support
- [ ] 🔜 Signal messenger
- [ ] 🔜 Claude (Anthropic) model
- [ ] 🔜 Multi-turn conversation memory
- [ ] 🔜 Skill: file read/write
- [ ] 🔜 Skill: code review
- [ ] 🔜 Auto-update via `/update`
- [ ] 🔜 Docker support

---

## 📝 License

MIT — Use it, modify it, share it. No strings attached.

---

<p align="center">
  <b>✦ Built with clarity. Runs on your terms. ✦</b>
</p>
