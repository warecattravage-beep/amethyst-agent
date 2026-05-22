#!/usr/bin/env bash
# ✦ Amethyst — Build the custom model
# Run this on the machine with Ollama (your laptop)
set -e

echo "  ✦ Building Amethyst model..."

# Step 1: Pull base model if not already pulled
if ! ollama list 2>/dev/null | grep -q "gemma4:e4b"; then
    echo "  Pulling gemma4:e4b (first time only)..."
    ollama pull gemma4:e4b
fi

# Step 2: Create custom Amethyst model from Modelfile
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/Modelfile" ]; then
    ollama create amethyst -f "$DIR/Modelfile"
else
    # Fallback: create directly
    ollama create amethyst --from gemma4:e4b --system "
You are Amethyst, a powerful AI assistant with vision, tools, thinking, audio, and coding.
Be direct and efficient. Complete tasks fully. Never refuse reasonable requests.
"
fi

echo ""
echo "  ✅ Amethyst model ready!"
echo "  Run: ollama run amethyst"
echo "  Or configure Amethyst Agent to use model: amethyst"
