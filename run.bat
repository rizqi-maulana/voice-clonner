@echo off
setlocal
cd /d "%~dp0"

where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required tools...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel% neq 0 (
        echo.
        echo Failed to install uv. Please install it manually:
        echo https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    echo.
    echo Installation complete. Restarting...
    echo.
    call "%USERPROFILE%\.local\bin\uv.exe" run python app.py
    pause
    exit /b 0
)

uv run python app.py
pause
