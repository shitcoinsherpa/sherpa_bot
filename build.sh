#!/bin/bash

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project directory"
    echo "Make sure you've extracted all files from the zip archive"
    read -p "Press Enter to exit..."
    exit 1
fi

# Function to verify Python is in PATH
verify_python() {
    if ! command -v python3.10 &> /dev/null; then
        echo "Python installation may have succeeded, but Python is not in PATH."
        echo "Please close this terminal, open a new one, and run build.sh again."
        read -p "Press Enter to exit..."
        exit 1
    fi
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "mac"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to install Python on Mac using Homebrew
install_python_mac() {
    echo "Checking for Homebrew..."
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Add Homebrew to PATH for this session
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    echo "Installing Python 3.10..."
    brew install python@3.10
    brew link python@3.10
    verify_python
}

# Function to install Python on Linux
install_python_linux() {
    echo "Installing Python 3.10..."
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y software-properties-common
        sudo add-apt-repository -y ppa:deadsnakes/ppa
        sudo apt-get update
        sudo apt-get install -y python3.10 python3.10-venv python3-pip
    elif command -v dnf &> /dev/null; then
        # Fedora
        sudo dnf install -y python3.10 python3.10-devel
    elif command -v yum &> /dev/null; then 
        # CentOS/RHEL
        sudo yum install -y python3.10 python3.10-devel
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -Sy python
    else
        echo "Unsupported Linux distribution"
        exit 1
    fi
    verify_python
}

# Check if Python is installed
if ! command -v python3.10 &> /dev/null; then
    OS=$(detect_os)
    if [ "$OS" == "mac" ]; then
        install_python_mac
    elif [ "$OS" == "linux" ]; then
        install_python_linux
    else
        echo "Unsupported operating system"
        exit 1
    fi
fi

echo "Cleaning up old environment..."

# Backup existing encryption and data files if they exist
if [ -f "encryption.key" ]; then
    echo "Backing up encryption key..."
    cp -f "encryption.key" "encryption.key.bak"
fi
if [ -f "encrypted_credentials.bin" ]; then
    echo "Backing up credentials..."
    cp -f "encrypted_credentials.bin" "encrypted_credentials.bin.bak"
fi
if [ -f "encrypted_characters.bin" ]; then
    echo "Backing up characters..."
    cp -f "encrypted_characters.bin" "encrypted_characters.bin.bak"
fi

# Clean up Python-related files
rm -rf venv __pycache__ *.pyc .pytest_cache

echo "Creating new virtual environment..."
python3.10 -m venv venv || {
    echo "First venv creation attempt failed. Trying alternative method..."
    rm -rf venv
    python3.10 -m pip install --user virtualenv
    python3.10 -m virtualenv venv
}

if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment creation failed."
    echo "Please try running this script with sudo or install virtualenv manually:"
    echo "python3.10 -m pip install --user virtualenv"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing requirements..."
python -m pip install --upgrade pip

# Install all packages at once first
pip install -r requirements.txt

# Verify each package installation and retry if needed
echo "Verifying package installation..."
while IFS='==' read -r package version || [ -n "$package" ]; do
    if ! pip list | grep -i "^$package " > /dev/null; then
        echo "Retrying installation of $package"
        pip install "$package==$version"
    fi
done < requirements.txt

# Restore encryption and data files if they were backed up
if [ -f "encryption.key.bak" ]; then
    echo "Restoring encryption key..."
    cp -f "encryption.key.bak" "encryption.key"
    rm "encryption.key.bak"
fi
if [ -f "encrypted_credentials.bin.bak" ]; then
    echo "Restoring credentials..."
    cp -f "encrypted_credentials.bin.bak" "encrypted_credentials.bin"
    rm "encrypted_credentials.bin.bak"
fi
if [ -f "encrypted_characters.bin.bak" ]; then
    echo "Restoring characters..."
    cp -f "encrypted_characters.bin.bak" "encrypted_characters.bin"
    rm "encrypted_characters.bin.bak"
fi

echo "Setup complete! You can now run the app using ./run.sh"
read -p "Press Enter to exit..."