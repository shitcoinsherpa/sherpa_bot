@echo off
setlocal enabledelayedexpansion

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Downloading Python 3.10...
    
    :: Check system architecture
    wmic os get osarchitecture | find "64-bit" > nul
    if errorlevel 1 (
        set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11.exe"
    ) else (
        set "PYTHON_URL=https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
    )
    
    :: Download Python installer
    echo Downloading from !PYTHON_URL!
    powershell -Command "(New-Object Net.WebClient).DownloadFile('!PYTHON_URL!', 'python_installer.exe')"
    
    :: Verify download
    if not exist python_installer.exe (
        echo Failed to download Python installer. Please check your internet connection.
        pause
        exit /b 1
    )
    
    echo Installing Python 3.10...
    :: Run installer with required parameters
    start /wait python_installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 Include_pip=1
    
    :: Clean up installer
    del python_installer.exe
    
    :: Update PATH without requiring refreshenv
    for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "PATH=%%b"
    for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v Path') do set "PATH=!PATH!;%%b"
    
    echo Python installation complete. Testing installation...
    
    :: Test if Python is now available
    python --version >nul 2>&1
    if errorlevel 1 (
        echo Python installation may have succeeded, but Python is not in PATH.
        echo Please close this window, open a new command prompt, and run build.bat again.
        pause
        exit /b 1
    )
)

echo Cleaning up old environment...

:: Backup existing encryption and data files if they exist
if exist "encryption.key" (
    echo Backing up encryption key...
    copy /Y "encryption.key" "encryption.key.bak" >nul
)
if exist "encrypted_credentials.bin" (
    echo Backing up credentials...
    copy /Y "encrypted_credentials.bin" "encrypted_credentials.bin.bak" >nul
)
if exist "encrypted_characters.bin" (
    echo Backing up characters...
    copy /Y "encrypted_characters.bin" "encrypted_characters.bin.bak" >nul
)

:: Clean up Python-related files
if exist "venv" rmdir /s /q "venv"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "*.pyc" del /f /q "*.pyc"
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"

echo Creating new virtual environment...
python -m venv venv
if not exist "venv\Scripts\activate.bat" (
    echo First venv creation attempt failed. Trying alternative method...
    rmdir /s /q venv
    python -m pip install --user virtualenv
    python -m virtualenv venv
)

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment creation failed.
    echo Please try running this script as administrator or install virtualenv manually:
    echo python -m pip install --user virtualenv
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing requirements...
python -m pip install --upgrade pip

:: Install all packages at once first
pip install -r requirements.txt

:: Then try to fix any that failed
pip list > installed_packages.txt
for /f "tokens=1,2 delims==" %%a in (requirements.txt) do (
    findstr /i /c:"%%a" installed_packages.txt >nul
    if errorlevel 1 (
        echo Installing %%a
        pip install "%%a%%b"
    )
)
del installed_packages.txt

:: Restore encryption and data files if they were backed up
if exist "encryption.key.bak" (
    echo Restoring encryption key...
    copy /Y "encryption.key.bak" "encryption.key" >nul
    del "encryption.key.bak"
)
if exist "encrypted_credentials.bin.bak" (
    echo Restoring credentials...
    copy /Y "encrypted_credentials.bin.bak" "encrypted_credentials.bin" >nul
    del "encrypted_credentials.bin.bak"
)
if exist "encrypted_characters.bin.bak" (
    echo Restoring characters...
    copy /Y "encrypted_characters.bin.bak" "encrypted_characters.bin" >nul
    del "encrypted_characters.bin.bak"
)

echo Setup complete! You can now run the app using run.bat
pause 