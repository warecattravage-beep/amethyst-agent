# ✦ Amethyst — Build & Install (Windows)
# Run this from the amethyst-agent-v3 folder
# Usage: .\build.ps1

Write-Host "  ✦ Building Amethyst model..." -ForegroundColor Cyan

# ── Step 1: Build the Ollama model ──
$hasModel = ollama list 2>$null | Select-String -Pattern "gemma4:e4b"
if (-not $hasModel) {
    Write-Host "  Pulling gemma4:e4b..." -ForegroundColor Yellow
    ollama pull gemma4:e4b
}

$modelfile = Join-Path $PSScriptRoot "Modelfile"
if (Test-Path $modelfile) {
    ollama create amethyst -f $modelfile
} else {
    ollama create amethyst --from gemma4:e4b --system "You are Amethyst, an AI assistant."
}

Write-Host "  ✅ Amethyst model created!" -ForegroundColor Green

# ── Step 2: Add to PATH so 'amethyst' works anywhere ──
$dir = $PSScriptRoot
$path = [Environment]::GetEnvironmentVariable("Path", "User")
if ($path -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable("Path", "$path;$dir", "User")
    Write-Host "  ✅ Added to PATH! Restart PowerShell and type: amethyst start" -ForegroundColor Cyan
} else {
    Write-Host "  ✅ Already in PATH" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "  Commands:        amethyst setup  |  amethyst start  |  amethyst dashboard"
Write-Host "  Run model:       ollama run amethyst"
Write-Host "  Restart needed:  Close and reopen PowerShell"
