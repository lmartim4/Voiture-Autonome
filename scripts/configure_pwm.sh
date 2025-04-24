#!/bin/bash

# Script to configure PWM on Raspberry Pi for the Voiture-Autonome project
# This script adds the necessary configuration to the config.txt file

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Checking sudo permissions
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script needs to be run as root (sudo)!${NC}"
    exit 1
fi

# File to be edited
CONFIG_FILE="/boot/firmware/config.txt"

# Line to be added
PWM_CONFIG="dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4"

# Checking if the file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}File $CONFIG_FILE not found!${NC}"
    echo -e "${YELLOW}Checking alternative location...${NC}"
    
    # In some versions of Raspberry Pi OS, the file may be in a different location
    ALT_CONFIG_FILE="/boot/config.txt"
    if [ -f "$ALT_CONFIG_FILE" ]; then
        echo -e "${GREEN}Configuration file found at $ALT_CONFIG_FILE${NC}"
        CONFIG_FILE="$ALT_CONFIG_FILE"
    else
        echo -e "${RED}Configuration file not found!${NC}"
        exit 1
    fi
fi

# Checking if the configuration already exists
if grep -q "$PWM_CONFIG" "$CONFIG_FILE"; then
    echo -e "${YELLOW}PWM configuration already exists in file $CONFIG_FILE${NC}"
    exit 0
fi

# Making a backup of the file
BACKUP_FILE="${CONFIG_FILE}.bak"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo -e "${YELLOW}Backup of configuration file created at $BACKUP_FILE${NC}"

# Adding the configuration to the end of the file
echo "$PWM_CONFIG" >> "$CONFIG_FILE"

# Checking if the addition was successful
if grep -q "$PWM_CONFIG" "$CONFIG_FILE"; then
    echo -e "${GREEN}PWM configuration successfully added to file $CONFIG_FILE${NC}"
    echo -e "${YELLOW}You will need to restart the Raspberry Pi to apply the changes.${NC}"
else
    echo -e "${RED}Failed to add PWM configuration!${NC}"
    echo -e "${YELLOW}Restoring backup...${NC}"
    cp "$BACKUP_FILE" "$CONFIG_FILE"
    exit 1
fi

exit 0