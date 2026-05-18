# ✦ Onyx — Build & Install (Windows)
# Run this from the onyx-agent-v3 folder
# Usage: .\build.ps1

Write-Host "  ✦ Building Onyx model..." -ForegroundColor Cyan

# ── Step 1: Build the Ollama model ──
$hasModel = ollama list 2>$null | Select-String -Pattern "gemma4:e4b"
if (-not $hasModel) {
    Write-Host "  Pulling gemma4:e4b..." -ForegroundColor Yellow
    ollama pull gemma4:e4b
}

$modelfile = Join-Path $PSScriptRoot "Modelfile"
if (Test-Path $modelfile) {
    ollama create onyx -f $modelfile
} else {
    ollama create onyx --from gemma4:e4b --system "You are Onyx, an AI assistant."
}

Write-Host "  ✅ Onyx model created!" -ForegroundColor Green

# ── Step 2: Add to PATH so 'onyx' works anywhere ──
$dir = $PSScriptRoot
$path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($path -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable("Path", "$path;$dir", "User")
    Write-Host "  ✅ Added to PATH! Restart PowerShell and type: onyx start" -ForegroundColor Cyan
} else {
    Write-Host "  ✅ Already in PATH" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  Commands:        onyx setup  |  onyx start  |  onyx dashboard"
Write-Host "  Run model:       ollama run onyx"
Write-Host "  Restart needed:  Close and reopen PowerShell"
