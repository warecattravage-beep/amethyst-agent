#!/data/data/com.termux/files/usr/bin/bash
# ───────────────────────────────────────────────────────────
# Onyx Agent — Termux setup for Android
# Run this in Termux on your Lenovo Yoga Tab 11
# ───────────────────────────────────────────────────────────
set -e

echo "✦ Onyx Agent — Android/Termux Setup"
echo

# ── 1. Update & install packages ──────────────────────────
echo "[1/5] Updating Termux packages..."
pkg update -y && pkg upgrade -y

echo "[2/5] Installing dependencies..."
pkg install -y python git curl wget cmake ninja build-essential

# ── 2. Install Ollama ──────────────────────────────────────
if command -v ollama &>/dev/null; then
    echo "[✓] Ollama already installed"
else
    echo "[3/5] Installing Ollama for Android (via official script)..."
    curl -fsSL https://ollama.com/install.sh | sh
fi

# ── 3. Pull the model ─────────────────────────────────────
echo "[4/5] Pulling gemma4:e4b (~4.5B params, edge-optimized)..."
ollama pull gemma4:e4b

# ── 4. Python deps ────────────────────────────────────────
echo "[5/5] Installing Python dependencies..."
pip install httpx

# ── Done ──────────────────────────────────────────────────
echo
echo "✦ Setup complete!"
echo
echo "  Next steps:"
echo "    1. Start Ollama:   ollama serve"
echo "    2. Launch agent:   cd onyx-agent && python cli.py"
echo
echo "  Or in one command:  ollama serve & python cli.py"
