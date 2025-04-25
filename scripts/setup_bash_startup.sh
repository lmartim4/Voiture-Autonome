#!/bin/bash

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
SOURCE_FILE="${SCRIPT_DIR}/.bash_quick_startup.sh"
DEST_FILE="${HOME}/.bash_quick_startup.sh"

if [ ! -f "$SOURCE_FILE" ]; then
    echo -e "${RED}Error: Source file $SOURCE_FILE not found!${NC}"
    exit 1
fi

if [ -f "$DEST_FILE" ]; then
    echo -e "${YELLOW}INFO: Destination file $DEST_FILE already exists!${NC}"
    echo -e "${YELLOW}If you want to re-install factory config, you must first delete the old file.${NC}"
    exit 0
fi

cp "$SOURCE_FILE" "$DEST_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Successfully installed .bash_quick_startup.sh to your home directory.${NC}"
    
    if grep -q "source ~/.bash_quick_startup.sh" "${HOME}/.bashrc"; then
        echo -e "${YELLOW}The script is already sourced in your .bashrc file.${NC}"
    else
        echo -e "\n# Source quick startup script" >> "${HOME}/.bashrc"
        echo "source ~/.bash_quick_startup.sh" >> "${HOME}/.bashrc"
        echo -e "${GREEN}Added source command to .bashrc. Changes will take effect in new terminal sessions.${NC}"
        echo -e "${YELLOW}To apply changes to current session, run: source ~/.bashrc${NC}"
    fi
else
    echo -e "${RED}Failed to copy the file to your home directory!${NC}"
    exit 1
fi

exit 0