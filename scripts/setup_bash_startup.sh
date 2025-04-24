#!/bin/bash
# ~/.bash_quick_startup.sh

RED='\033[1;31m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
CYAN='\033[1;36m'
NC='\033[0m'  # No Color

# Change to the project directory
cd ~/Voiture-Autonome/code || { echo -e "${RED}Error: Directory not found!${NC}"; exit 1; }

# Activate the virtual environment and check if it was successful
if source ./venv/bin/activate; then
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${GREEN}        Welcome to Voiture Jaune!${NC}"
  echo -e "${YELLOW}=============================================${NC}"
  echo -e "${CYAN}Current Date: ${NC}$(date)"
  echo -e "${CYAN}User:         ${NC}$(whoami)"
  echo -e "${CYAN}Project Dir:  ${NC}~/Voiture-Autonome/code"
  echo -e "${YELLOW}--------------------------------------------${NC}"
  echo -e "${YELLOW}NOTE: ${NC}You are now in a Python virtual environment"
  echo -e "      Type ${GREEN}deactivate${NC} to exit the environment"
  echo -e "${YELLOW}=============================================${NC}"

  # Clean Command History and Preload with Three Commands
  history -c
  history -w

  # Add only the three desired commands to the history (in order)
  history -s "python multiplot.py"
  history -s "python calibrate.py"
  history -s "python main.py"
else
  echo -e "${RED}Error: Could not activate virtual environment!${NC}"
fi