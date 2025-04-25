#!/bin/bash

# Main installation script for Autonomous-Vehicle project

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to display error messages but continue execution
error_continue() {
    echo -e "${RED}ERROR: $1${NC}"
    echo -e "${YELLOW}Continuing with next steps...${NC}"
    FAILED_STEPS+=("$2")
}

# Function to display error messages and exit
error_exit() {
    echo -e "${RED}ERROR: $1${NC}"
    exit 1
}

# Function to display success messages
success_message() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Function to display information messages
info_message() {
    echo -e "${YELLOW}INFO: $1${NC}"
}

# Array to track failed steps
FAILED_STEPS=()

# Checking if we are on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/device-tree/model 2>/dev/null; then
    error_exit "This script must be executed on a Raspberry Pi!"
fi

# Checking if the project directory exists in the correct location
PROJECT_DIR=~/Voiture-Autonome
if [ ! -d "$PROJECT_DIR" ]; then
    error_exit "Project directory not found at $PROJECT_DIR! Please clone the repository first."
fi

# Checking sudo permissions
if [ "$EUID" -ne 0 ]; then
    info_message "This script requires sudo permissions for some operations."
    if ! sudo -n true 2>/dev/null; then
        echo "Please enter your sudo password:"
        sudo -v || error_exit "Failed to obtain sudo permissions!"
    fi
fi

# Changing to the project directory
cd "$PROJECT_DIR" || error_exit "Could not access the project directory!"

# Checking if the scripts directory exists
if [ ! -d "$PROJECT_DIR/scripts" ]; then
    error_exit "Scripts directory not found at $PROJECT_DIR/scripts! Check the repository structure."
fi

# Checking if the necessary scripts exist
SCRIPTS=(
    "./scripts/configure_pwm.sh"
    "./scripts/configure_udev.sh"
    "./scripts/setup_bash_startup.sh"
    "./scripts/install_dependencies.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ ! -f "$script" ]; then
        error_exit "Script $script not found! Check the repository structure."
    fi
done

# Making scripts executable
chmod +x ./scripts/*.sh || error_exit "Failed to make scripts executable!"

# Running individual scripts in the correct order
info_message "Starting installation process..."

echo "1/4 - Configuring PWM..."
if sudo "./scripts/configure_pwm.sh"; then
    success_message "PWM configuration completed!"
else
    error_continue "Failed in PWM configuration!" "PWM Configuration"
fi

echo "2/4 - Configuring udev rules..."
if sudo "./scripts/configure_udev.sh"; then
    success_message "udev configuration completed!"
else
    error_continue "Failed in udev configuration!" "udev Configuration"
fi

echo "3/4 - Installing dependencies..."
if "./scripts/install_dependencies.sh"; then
    success_message "Dependencies installation completed!"
else
    error_continue "Failed to install dependencies!" "Dependencies Installation"
fi

echo "4/4 - Setting up quick start script..."
if "./scripts/setup_bash_startup.sh"; then
    success_message "Startup script configuration completed!"
else
    error_continue "Failed to configure startup script!" "Startup Script Configuration"
fi

# Finalizing installation with summary of results
echo ""
echo "=== Installation Summary ==="
if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
    success_message "Autonomous-Vehicle project installation completed successfully!"
else
    echo -e "${YELLOW}Installation completed with some errors:${NC}"
    for step in "${FAILED_STEPS[@]}"; do
        echo -e "  - ${RED}Failed: $step${NC}"
    done
    echo -e "${YELLOW}You may need to manually complete these steps or troubleshoot the issues.${NC}"
fi

info_message "Restart the system to apply all configurations: sudo reboot"

exit 0