@echo off
REM Amethyst NPU build script — for Intel AI Boost
REM Run this on your Windows laptop with NPU

echo.
echo   Building Amethyst-NPU for Intel AI Boost...
echo.

REM Pull base model
ollama pull qwen2.5:0.5b

REM Create NPU-optimized model
cd /d "%~dp0"
if exist Modelfile.npu (
    ollama create amethyst-npu -f Modelfile.npu
) else (
    ollama create amethyst-npu --from qwen2.5:0.5b --system "You are Amethyst-NPU, a fast assistant for quick queries."
)

echo.
echo   NPU model ready! Run: ollama run amethyst-npu
echo.
echo   Your full Amethyst model stays for heavy work: ollama run amethyst
echo.
