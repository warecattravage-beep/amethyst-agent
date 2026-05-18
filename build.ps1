# ✦ Onyx — Build the custom model
# Run this on Windows with Ollama installed
# Usage: .\build.ps1

Write-Host "  ✦ Building Onyx model..." -ForegroundColor Cyan

# Step 1: Check if base model exists
$hasModel = ollama list 2>$null | Select-String -Pattern "gemma4:e4b"
if (-not $hasModel) {
    Write-Host "  Pulling gemma4:e4b (first time only)..." -ForegroundColor Yellow
    ollama pull gemma4:e4b
}

# Step 2: Create custom Onyx model
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$modelfile = Join-Path $scriptDir "Modelfile"

if (Test-Path $modelfile) {
    ollama create onyx -f $modelfile
} else {
    # Fallback inline
    $system = @"
You are Onyx, a powerful AI assistant with vision, tools, thinking, audio, and coding capabilities.
Be direct and efficient. Complete tasks fully. Never refuse reasonable requests.
"@
    ollama create onyx --from gemma4:e4b --system $system
}

Write-Host ""
Write-Host "  ✅ Onyx model ready!" -ForegroundColor Green
Write-Host "  Run: ollama run onyx" -ForegroundColor Cyan
Write-Host "  Or configure Onyx Agent to use model: onyx" -ForegroundColor Cyan
