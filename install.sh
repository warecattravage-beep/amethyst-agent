#!/usr/bin/env bash
set -e

# ── ✦ Onyx Agent — Smart Installer ──
# Cross-platform: Linux / Windows / Termux (Android)
# Installs deps, creates config, sets up dashboard mode per platform.

BOLD='\033[1m'
CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── ASCII Banner ──
echo -e "${CYAN}"
echo '      ██████╗ ███╗   ██╗██╗   ██╗██╗  ██╗'
echo '     ██╔═══██╗████╗  ██║╚██╗ ██╔╝╚██╗██╔╝'
echo '     ██║   ██║██╔██╗ ██║ ╚████╔╝  ╚███╔╝'
echo '     ██║   ██║██║╚██╗██║  ╚██╔╝   ██╔██╗'
echo '     ╚██████╔╝██║ ╚████║   ██║   ██╔╝ ██╗'
echo '      ╚═════╝ ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝'
echo ''
echo '       ██████╗  █████╗ ████████╗███████╗'
echo '      ██╔════╝ ██╔══██╗╚══██╔══╝██╔════╝'
echo '      ██║  ███╗███████║   ██║   █████╗'
echo '      ██║   ██║██╔══██║   ██║   ██╔══╝'
echo '      ╚██████╔╝██║  ██║   ██║   ███████╗'
echo '       ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚══════╝'
echo -e "${NC}"
echo -e "${BOLD}         ✦ Standalone Agent Gateway ✦${NC}"
echo ''

# ── Detect platform ──
PLATFORM="unknown"
if [ -n "$TERMUX_VERSION" ] || echo "$PWD" | grep -q "com.termux"; then
    PLATFORM="termux"
elif [ -f "/proc/version" ] && grep -qi microsoft /proc/version 2>/dev/null; then
    PLATFORM="wsl"
elif [ "$(uname)" = "Linux" ]; then
    PLATFORM="linux"
elif [ "$(uname)" = "Darwin" ]; then
    PLATFORM="macos"
elif [ "$(uname -o 2>/dev/null)" = "Msys" ] || [ -n "$MSYSTEM" ]; then
    PLATFORM="windows"
fi

echo -e "  ${BOLD}Platform:${NC} ${CYAN}${PLATFORM}${NC}"
echo ""

# ── Python check ──
PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        PYTHON=$cmd
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "  ${RED}✗ Python not found. Please install Python 3.10+${NC}"
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo -e "  ${BOLD}Python:${NC} ${GREEN}${PYVER}${NC}"
echo ""

# ── Detect package manager ──
if command -v pkg &>/dev/null; then
    PKG="pkg install -y"
elif command -v apt-get &>/dev/null; then
    PKG="sudo apt-get install -y"
elif command -v brew &>/dev/null; then
    PKG="brew install"
elif command -v pacman &>/dev/null; then
    PKG="sudo pacman -S --noconfirm"
else
    PKG=""
fi

# ── Install per platform ──
case "$PLATFORM" in
    termux)
        echo -e "  ${YELLOW}[Termux] Installing system packages...${NC}"
        pkg update -y 2>/dev/null || true
        pkg install -y python clang python-pip git 2>/dev/null || true
        pip install httpx 2>/dev/null || pip3 install httpx 2>/dev/null || true
        echo -e "  ${GREEN}✓ Termux ready${NC}"
        echo -e "  ${CYAN}  Dashboard: web mode → http://localhost:9091${NC}"
        ;;

    linux)
        echo -e "  ${YELLOW}[Linux] Installing Kivy deps + optional packages...${NC}"
        if [ -n "$PKG" ] && echo "$PKG" | grep -q "apt-get"; then
            $PKG python3-dev python3-pip libsdl2-dev libsdl2-image-dev \
                  libsdl2-mixer-dev libsdl2-ttf-dev libportmidi-dev \
                  libgstreamer1.0-dev gstreamer1.0-plugins-good 2>/dev/null || true
        fi
        pip3 install --user kivy httpx openai anthropic 2>/dev/null || \
        python3 -m pip install --user kivy httpx openai anthropic 2>/dev/null || true
        echo -e "  ${GREEN}✓ Linux ready${NC}"
        echo -e "  ${CYAN}  Dashboard: Kivy GUI${NC}"
        echo -e "  ${CYAN}  Web mode:   python3 onyx.py dashboard --web${NC}"
        ;;

    windows|wsl)
        echo -e "  ${YELLOW}[Windows] Installing packages...${NC}"
        pip install kivy httpx openai anthropic 2>/dev/null || \
        python -m pip install kivy httpx openai anthropic 2>/dev/null || true
        echo -e "  ${GREEN}✓ Windows ready${NC}"
        ;;

    *)
        echo -e "  ${YELLOW}[${PLATFORM}] Installing core deps...${NC}"
        pip install --user httpx 2>/dev/null || true
        ;;
esac

# ── Create default config ──
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f "config.json" ]; then
    echo -e "\n  ${YELLOW}Creating default config.json...${NC}"
    if $PYTHON -c "import sys; sys.path.insert(0, '.'); from core.config import Config; Config('config.json')" 2>/dev/null; then
        echo -e "  ${GREEN}✓ Default config created${NC}"
    else
        cat > config.json << 'EOF'
{
  "agent_name": "Onyx",
  "active_model": "ollama",
  "active_messengers": ["console"],
  "messengers": {
    "console": {"enabled": true, "prompt": "onyx> "},
    "telegram": {"enabled": false, "token": ""},
    "discord": {"enabled": false, "token": ""},
    "signal": {"enabled": false, "cli_path": "signal-cli", "account": ""}
  },
  "models": {
    "ollama": {"enabled": true, "host": "http://localhost:11434", "model": "gemma2:9b"},
    "openai": {"enabled": false, "api_key": "", "model": "gpt-4o"}
  },
  "skills": {
    "chat": {"enabled": true},
    "coding": {"enabled": true},
    "terminal": {"enabled": true},
    "web_search": {"enabled": true},
    "web_fetch": {"enabled": true}
  },
  "data_dir": "data",
  "log_file": "data/onyx.log",
  "log_level": "INFO"
}
EOF
        echo -e "  ${GREEN}✓ Default config created${NC}"
    fi
fi

chmod +x onyx.py

# ── Add to PATH so 'onyx' works from anywhere ──
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

PATH_LINE="export PATH=\"\$PATH:$SCRIPT_DIR\""
if ! grep -q "$SCRIPT_DIR" "$SHELL_RC" 2>/dev/null; then
    echo "" >> "$SHELL_RC"
    echo "# Onyx Agent" >> "$SHELL_RC"
    echo "$PATH_LINE" >> "$SHELL_RC"
    echo -e "  ${GREEN}✓ Added to PATH in $SHELL_RC${NC}"
    echo -e "  ${CYAN}  Type: onyx start${NC}"
    echo -e "  ${CYAN}  Or reload: source $SHELL_RC${NC}"
else
    echo -e "  ${GREEN}✓ PATH already configured${NC}"
fi

# ── Done ──
echo ""
echo -e "${GREEN}  ═══════════════════════════════════════${NC}"
echo -e "${GREEN}   ✦ Onyx Agent Gateway — Installed! ✦${NC}"
echo -e "${GREEN}  ═══════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Quick Start:${NC}"
echo -e "  ${CYAN}  source $SHELL_RC${NC}           Reload shell config"
echo -e "  ${CYAN}  onyx setup${NC}                 First-time config"
echo -e "  ${CYAN}  onyx start${NC}                 Launch the agent"
echo -e "  ${CYAN}  onyx dashboard${NC}             Open dashboard"
echo -e "  ${CYAN}  onyx config${NC}                Edit config"
echo ""
echo -e "  ${BOLD}Gateway Features:${NC}"
echo -e "  • Multi-messenger routing (Telegram / Discord / Console)"
echo -e "  • AI model switching (Ollama / OpenAI / Claude)"
echo -e "  • Plugin skills (coding / terminal / web search)"
echo -e "  • Config dashboard per platform"
echo ""

case "$PLATFORM" in
    termux|linux)
        read -p "  Run setup wizard now? [Y/n]: " ans
        if [ "${ans:-Y}" != "n" ] && [ "${ans:-Y}" != "N" ]; then
            $PYTHON onyx.py setup
        fi
        ;;
esac

echo -e "\n  ${CYAN}✦ Gateway online. Let's build.${NC}\n"
