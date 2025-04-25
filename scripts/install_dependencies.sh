#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

error_exit() {
    echo -e "${RED}ERROR: $1${NC}"
    exit 1
}

success_message() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

info_message() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

info_message "Checking Python installation..."

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    info_message "Python $PYTHON_VERSION found."
else
    error_exit "Python 3 not found on the system. Please install Python 3 and try again."
fi

info_message "Checking internet connection..."

if ! ping -c 1 google.com &> /dev/null; then
    error_exit "No internet connection! Please check your connection and try again."
fi

info_message "Updating package list..."
sudo apt-get update || error_exit "Failed to update repositories!"

info_message "Installing required system packages..."
sudo apt-get install -y python3-tk python3-pil.imagetk || error_exit "Failed to install required packages!"

if [ ! -d "code" ]; then
    error_exit "No code folder... Have you clonned the right repo?"
fi

cd code || error_exit "Failed to change to code directory!"

info_message "Creating virtual environment in code subfolder..."
python3 -m venv --system-site-packages venv || error_exit "Failed to create virtual environment!"

success_message "Virtual environment created successfully in the code folder."

info_message "Activating virtual environment and installing requirements..."
source venv/bin/activate || error_exit "Failed to activate virtual environment!"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt || error_exit "Failed to install requirements!"
    success_message "Requirements installed successfully."
else
    error_exit "requirements.txt file not found in the code directory!"
fi

success_message "Setup completed successfully! The virtual environment is activated."
info_message "To deactivate the virtual environment, type 'deactivate'"

exit 0