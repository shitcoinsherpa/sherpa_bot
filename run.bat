@echo off

:: Check if we're in the right directory
if not exist "requirements.txt" (
    echo Error: Please run this script from the project directory
    echo Make sure you've extracted all files from the zip archive
    pause
    exit /b 1
)

echo Activating virtual environment...
if not exist "venv" (
    echo Error: Virtual environment not found
    echo Please run build.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Starting Twitter Bot Control Center...
start http://127.0.0.1:7860
python sherpa_bot.py

if errorlevel 1 (
    echo Error running the application. Press any key to exit...
    pause
) 