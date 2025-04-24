# Quick Terminal Start-Up trick

This is a simple bash script that facilitates the voiture's starting up process. It has the following features that speeds up this process: 

- Automatically navigates to project directory
- Activates Python virtual environment
- Pre-loads command history with key commands
- Shows a colorful welcome message

## Installation

1. Save the script as `~/.bash_quick_startup.sh`
2. Make it executable:
   ```bash
   chmod +x ~/.bash_quick_startup.sh
   ```
3. Add to your `.bashrc`:
   ```bash
   if [ -f ~/.bash_quick_startup.sh ]; then
      source ~/.bash_quick_startup.sh
   fi
   ```

## Usage

Simply open up a new terminal and:
- Press Up Arrow ↑ to select `python main.py`
- Press Enter to run

## Disabling Temporarily

Sometimes you might need to quit this venv in order to run some commands outside the venv. 

* When installing picamera2 for the first time. This specific module should be installed outside the venv and be imported by allowing the venv to "include-system-site-packages". You might check it by reading "/venv/pyvenv.cfg"


To exit the environment and use the terminal normally:

```bash
deactivate
```


## .bash_quick_startup.sh
```bash
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
```