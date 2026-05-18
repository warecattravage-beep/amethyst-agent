# ✦ Onyx Agent Gateway

> **Your own personal AI agent — runs entirely on your machine.**
> Multi-messenger, multi-model, plugin skills, configurable persona, and proactive conversation. All local, all yours.

```
    ██████╗  ███╗  ██╗ ██╗  ██╗ ██╗  ██╗
   ██╔═══██╗ ████╗ ██║ ╚██╗ ██╔╝ ╚██╗██╔╝
   ██║   ██║ ██╔██╗██║  ╚████╔╝   ╚███╔╝
   ██║   ██║ ██║╚████║   ╚██╔╝    ██╔██╗
   ╚██████╔╝ ██║ ╚███║    ██║    ██╔╝ ██╗
    ╚═════╝  ╚═╝  ╚══╝    ╚═╝    ╚═╝  ╚═╝
           ✦ Onyx Agent Gateway ✦
```

---

## ✨ Features

### 🧠 Persona-Driven AI
Configure your agent's personality during setup — *"Friendly coding buddy"*, *"Efficient sysadmin"*, *"Creative storyteller"*. The persona is baked into every conversation and adjustable anytime.

### 💬 Multi-Messenger
Speak to your agent through **Telegram**, **Discord**, **console terminal**, or **Signal** (via signal-cli). Toggle messengers on/off from the dashboard.

### 🧠 Multi-Model
Swap between **Ollama** (local, free, private) and **OpenAI** (GPT-4o) backends. Switch anytime with `/models` or the dashboard.

### 🔧 Plugin Skills (11 total)
| Skill | What it does |
|---|---|
| 💬 `chat` | General conversation (always on) |
| 💻 `coding` | Write + run Python, bash, Node.js in a sandbox |
| 🖥️ `terminal` | Run shell commands (blocklist-safe) |
| 🌐 `web_search` | Search Brave / DuckDuckGo |
| 📄 `web_fetch` | Fetch any URL and extract text |
| 📁 `file` | Read and write files |
| 🔍 `code_review` | Review code from files |
| 📂 `project` | Create multi-file projects under ~/Projects/ |
| 📝 `notion` | Query/create Notion pages and databases |
| 🔍 `search` | Search past conversations (RAG memory) |
| 🔄 `self_heal` | Auto-retry failed skills with fixes |

### 💬 Proactive Conversation
The agent can message you unprompted after 10 minutes of idle time — random check-ins, max once per 30 minutes. Configurable or disableable.

### 🧠 Conversation Memory + RAG
Remembers past messages per chat (up to 10 exchanges). Ask a question, follow up with *"explain more"* — it remembers context. **RAG memory** lets you `/search` across all past conversations using keyword matching.

### 🖥️ Dashboards
- **Desktop (Linux/Windows):** Kivy native GUI
- **Termux (Android):** Web dashboard at `localhost:9091`
- **CLI:** `onyx status` for quick overview

### 🎨 Visual Polish
- Violet-colored ASCII art banner on startup
- Color-coded log output (by module + severity)
- Typing indicator in Telegram while AI thinks

---

## 🚀 Quick Start

**Linux / Termux:**
```bash
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
onyx setup
onyx start
```

**Windows:**
```powershell
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
pip install httpx kivy openai
python onyx.py setup
python onyx.py start
```

> After `bash install.sh`, the `onyx` command is available system-wide.
> On Termux: runs via web dashboard at `http://localhost:9091`

---

## 📟 Commands

| Command | What it does |
|---|---|
| `onyx setup` | 🎯 Step-by-step onboarding wizard (identity, model, Telegram, proactive, Notion) |
| `onyx start` | ▶️ Launch the agent gateway |
| `onyx dashboard` | 🖥️ Open GUI or web dashboard |
| `onyx dashboard --web` | 🌐 Force web dashboard |
| `onyx status` | 📊 CLI overview |
| `onyx config` | 📝 Edit config.json |
| `onyx logs` | 📋 View recent logs |

**While running:**
- `/help` — Show commands
- `/status` — System status
- `/models` — List/switch AI models
- `/skills` — Show enabled skills
- `/clear` — Clear conversation memory
- `/update` — Git pull + restart
- `/quit` — Exit

---

## 🧠 Persona Setup

During `onyx setup`, you'll be asked:

```
Persona — How should Onyx behave?
  Examples:
    'Friendly coding buddy who explains everything simply'
    'Efficient sysadmin — short answers, no fluff'
    'Creative storyteller with a dark sense of humor'
```

This becomes the agent's personality in every response. Change it anytime by editing `agent_vibe` in `config.json` or re-running `onyx setup`.

---

## ✈️ Messengers

```json
"messengers": {
  "console":  {"enabled": true,  "prompt": "onyx> "},
  "telegram": {"enabled": true,  "token": "7865432:AAHd8s9a..."},
  "discord":  {"enabled": false, "token": ""},
  "signal":   {"enabled": false, "cli_path": "signal-cli", "account": ""}
}
```

> **Telegram:** Create a bot via [@BotFather](https://t.me/BotFather), paste the token.

---

## 🧠 Models

```json
"models": {
  "ollama": {
    "enabled": true,
    "host": "http://localhost:11434",
    "model": "gemma2:2b"
  },
  "openai": {
    "enabled": false,
    "api_key": "sk-...",
    "model": "gpt-4o"
  }
}
```

- **Ollama:** Free, local, private. Pull models with `ollama pull <name>`.
- **OpenAI:** Cloud GPT models. Requires API key.

---

## 💬 Proactive Mode

When enabled, the agent messages you unprompted after being idle:
- ⏱ Checks after **10 minutes** of silence
- 🎲 **40% random chance** to actually send (unpredictable)
- 🔁 Max **once per 30 minutes**
- 🌙 Quiet hours: 11 PM — 8 AM (auto-respects)

Configurable in `config.json` under `"proactive"` or toggle during setup.

---

## 🖥️ Dashboards

| Platform | Type | Launch |
|---|---|---|
| 🐧 Linux | Kivy GUI | `onyx dashboard` |
| 🪟 Windows | Kivy GUI | `onyx dashboard` |
| 📱 Termux | 🌐 Web UI | `onyx dashboard` → `localhost:9091` |
| 🌐 Any | Web UI | `onyx dashboard --web` |

The web dashboard is a full SPA with tabs for Status, Messengers, Models, Skills, Config, and Logs — zero extra dependencies.

---

## 🏗️ Architecture

```
📁 onyx-agent/
├── 📄 onyx.py              CLI entry (also at $PREFIX/bin/onyx)
├── 📄 config.json          All settings
├── 📄 install.sh           Cross-platform installer
│
├── 📁 core/
│   ├── 📄 config.py        JSON config with dot-notation
│   ├── 📄 engine.py        Message router + lifecycle (550 lines)
│   ├── 📄 memory.py        Conversation history manager
│   ├── 📄 setup_wizard.py  Lightweight setup (no rich)
│   ├── 📄 messenger.py     Base messenger interface
│   ├── 📄 model.py         Base AI model interface
│   └── 📄 skill.py         Base skill interface
│
├── 📁 messengers/
│   ├── 📄 console.py       Terminal chat (rich fallback to plain)
│   ├── 📄 telegram.py      Telegram bot (HTTP polling + typing)
│   └── 📄 discord.py       Discord bot (HTTP API)
│
├── 📁 models/
│   ├── 📄 ollama.py        Local LLM via Ollama
│   └── 📄 openai.py        OpenAI / OpenRouter API
│
├── 📁 skills/
│   ├── 📄 chat.py          General conversation
│   ├── 📄 coding.py        Code execution sandbox
│   ├── 📄 terminal.py      Shell commands (safe blocklist)
│   ├── 📄 web_search.py    Brave / DuckDuckGo
│   ├── 📄 web_fetch.py     URL content extraction
│   ├── 📄 file_skill.py    File read/write
│   └── 📄 code_review.py   Code review
│
└── 📁 dashboard/
    ├── 📄 app.py           Kivy native GUI (desktop)
    ├── 📄 web_dashboard.py Web UI (Termux/fallback)
    └── 📄 dashboard.py     CLI text dashboard
```

---

## 📦 Per-Platform Install

**Linux:**
```bash
sudo apt install python3 python3-pip git
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
```

**Windows:**
```powershell
pip install httpx kivy openai
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
python onyx.py setup
python onyx.py start
```

**Termux (Android):**
```bash
pkg install python git
git clone https://github.com/warecattravage-beep/onyx-agent-v3.git
cd onyx-agent-v3
bash install.sh
onyx setup
onyx start
# Dashboard: http://localhost:9091
```

---

## 🗺️ Roadmap

- [x] ✅ Console, Telegram, Discord messengers
- [x] ✅ Ollama + OpenAI models
- [x] ✅ 11 plugin skills
- [x] ✅ Conversation memory + RAG search
- [x] ✅ Configurable persona
- [x] ✅ Proactive mode (random check-ins, max 5/day)
- [x] ✅ Autonomous mode (15-step reasoning)
- [x] ✅ Self-healing (auto-retry failed skills)
- [x] ✅ Project mode (multi-file projects)
- [x] ✅ Notion integration
- [x] ✅ Auto-update (checks GitHub every 30 min)
- [x] ✅ Colorful logs + violet ASCII banner
- [x] ✅ Kivy GUI + Web dashboard
- [x] ✅ Typing indicator (Telegram)
- [x] ✅ Step-by-step onboarding wizard
- [x] ✅ Cross-platform (Linux, Windows, Termux)
- [ ] 🔜 Docker support
- [ ] 🔜 Plugin auto-loader

---

## 📝 License

MIT — Use it, modify it, share it. No strings attached.

---

<p align="center">
  <b>✦ Built with clarity. Runs on your terms. ✦</b>
</p>
