#!/usr/bin/env bash
# ✦ Onyx — Build the custom model
# Run this on the machine with Ollama (your laptop)
set -e

echo "  ✦ Building Onyx model..."

# Step 1: Pull base model if not already pulled
if ! ollama list 2>/dev/null | grep -q "gemma4:e4b"; then
    echo "  Pulling gemma4:e4b (first time only)..."
    ollama pull gemma4:e4b
fi

# Step 2: Create custom Onyx model from Modelfile
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/Modelfile" ]; then
    ollama create onyx -f "$DIR/Modelfile"
else
    # Fallback: create directly
    ollama create onyx --from gemma4:e4b --system "
You are Onyx, a powerful AI assistant with vision, tools, thinking, audio, and coding.
Be direct and efficient. Complete tasks fully. Never refuse reasonable requests.
"
fi

echo ""
echo "  ✅ Onyx model ready!"
echo "  Run: ollama run onyx"
echo "  Or configure Onyx Agent to use model: onyx"
