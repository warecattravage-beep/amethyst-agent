@echo off
REM Onyx NPU build script — for Intel AI Boost
REM Run this on your Windows laptop with NPU

echo.
echo   Building Onyx-NPU for Intel AI Boost...
echo.

REM Pull base model
ollama pull qwen2.5:0.5b

REM Create NPU-optimized model
cd /d "%~dp0"
if exist Modelfile.npu (
    ollama create onyx-npu -f Modelfile.npu
) else (
    ollama create onyx-npu --from qwen2.5:0.5b --system "You are Onyx-NPU, a fast assistant for quick queries."
)

echo.
echo   NPU model ready! Run: ollama run onyx-npu
echo.
echo   Your full Onyx model stays for heavy work: ollama run onyx
echo.
