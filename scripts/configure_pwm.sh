#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Checking sudo permissions
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script needs to be run as root (sudo)!${NC}"
    exit 1
fi

CONFIG_FILE="/boot/firmware/config.txt"
PWM_CONFIG="dtoverlay=pwm-2chan,pin=12,func=4,pin2=13,func2=4"

# Checking if the configuration already exists
if grep -q "$PWM_CONFIG" "$CONFIG_FILE"; then
    echo -e "${YELLOW}PWM configuration already exists in file $CONFIG_FILE${NC}"
    echo -e "${YELLOW}If it is not working try rebooting the system.${NC}"
    exit 0
fi

echo "$PWM_CONFIG" >> "$CONFIG_FILE"

if grep -q "$PWM_CONFIG" "$CONFIG_FILE"; then
    echo -e "${GREEN}PWM configuration successfully added to file $CONFIG_FILE${NC}"
    echo -e "${YELLOW}You will need to restart the Raspberry Pi to apply the changes.${NC}"
else
    echo -e "${RED}Failed to add PWM configuration!${NC}"
    exit 1
fi

exit 0