#!/bin/bash
# ~/.bash_quick_startup.sh

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'  # No Color

# Change to the project directory
cd ~/Voiture-Autonome/code || { echo -e "${RED}Error: Directory not found!${NC}"; echo -e "${YELLOW}You might need to clone project repository and re-run install.sh!${NC}"; }

# Activate the virtual environment and check if it was successful
if source ./venv/bin/activate; then
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${GREEN}        Welcome to $(hostname)!${NC}"
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${CYAN}Current Date: ${NC}$(date)"
  echo -e "${CYAN}User:         ${NC}$(whoami)"
  echo -e "${CYAN}Project Dir:  ${NC}~/Voiture-Autonome/code"
  echo -e "${YELLOW}--------------------------------------------${NC}"
  echo -e "${YELLOW}NOTE: ${NC}You are now in a Python virtual environment"
  echo -e "      Type ${RED}deactivate${NC} to exit the environment"
  echo -e "${YELLOW}=============================================${NC}"

  # Clean Command History and Preload with Three Commands
  history -c
  history -w

  # Add only the three desired commands to the history (in order)
  
  history -s "python multiplot.py"
  history -s "python plot_steer_constants.py"
  history -s "python interface_motor.py"
  history -s "python interface_steer.py"
  history -s "python interface_serial.py"
  history -s "python interface_camera.py"
  history -s "python interface_lidar.py"
  history -s "python calibrate.py"
  history -s "python main.py"
else
  echo -e "${RED}Error: Could not activate virtual environment!${NC}"
fi

