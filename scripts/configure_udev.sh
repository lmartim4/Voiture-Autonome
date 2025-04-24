#!/bin/bash

# Script to configure udev rules for devices in the Voiture-Autonome project
# This script creates/modifies the udev rules file for Arduino and USB devices

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[38;5;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}  Voiture-Autonome Device Configuration Script          ${NC}"
echo -e "${BLUE}=========================================================${NC}"
echo -e "${YELLOW}This script configures your system to recognize:${NC}"
echo -e "  • Arduino Nano 33 BLE (or similar) - will be mapped to /dev/ttyACM"
echo -e "  • LiDAR sensor (using CP210x bridge) - will be mapped to /dev/ttyUSB"
echo ""

# Checking sudo permissions
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script needs to be run as root (sudo)!${NC}"
    echo -e "${YELLOW}Please run: sudo $0${NC}"
    exit 1
fi

# udev rules file
UDEV_RULES_FILE="/etc/udev/rules.d/99-voiture-autonome.rules"

# udev rules content with detailed comments
ARDUINO_RULE="# Arduino Nano 33 BLE (vendor: 2341, product: 8057)\nSUBSYSTEM==\"tty\", ATTRS{idVendor}==\"2341\", ATTRS{idProduct}==\"8057\", SYMLINK+=\"ttyACM\", GROUP=\"dialout\", MODE=\"0666\""
USB_RULE="# LiDAR sensor with Silicon Labs CP210x USB to UART bridge (vendor: 10c4, product: ea60)\nSUBSYSTEM==\"tty\", ATTRS{idVendor}==\"10c4\", ATTRS{idProduct}==\"ea60\", SYMLINK+=\"ttyUSB\", GROUP=\"dialout\", MODE=\"0666\""

# Check if the current user is in the dialout group
if ! groups | grep -q '\bdialout\b'; then
    echo -e "${YELLOW}Note: Current user is not in the 'dialout' group${NC}"
    echo -e "${YELLOW}Adding user '$(whoami)' to 'dialout' group for device access${NC}"
    usermod -a -G dialout $(logname)
    echo -e "${YELLOW}Please log out and back in for group changes to take effect${NC}"
fi

# Creating the directory if it doesn't exist
if [ ! -d "/etc/udev/rules.d" ]; then
    echo -e "${YELLOW}Creating directory /etc/udev/rules.d${NC}"
    mkdir -p /etc/udev/rules.d
fi

# Function to detect currently connected devices
detect_devices() {
    echo -e "\n${BLUE}Detecting currently connected devices...${NC}"
    
    # Check for Arduino devices
    if lsusb | grep -q "2341:8057"; then
        echo -e "${GREEN}✓ Arduino device detected (VendorID:ProductID - 2341:8057)${NC}"
        ARDUINO_DETECTED=1
    else
        echo -e "${YELLOW}× No Arduino device currently connected${NC}"
        ARDUINO_DETECTED=0
    fi
    
    # Check for LiDAR devices
    if lsusb | grep -q "10c4:ea60"; then
        echo -e "${GREEN}✓ LiDAR device detected (VendorID:ProductID - 10c4:ea60)${NC}"
        LIDAR_DETECTED=1
    else
        echo -e "${YELLOW}× No LiDAR device currently connected${NC}"
        LIDAR_DETECTED=0
    fi
}

# Backup existing rules file if it exists
if [ -f "$UDEV_RULES_FILE" ]; then
    BACKUP_FILE="${UDEV_RULES_FILE}.bak.$(date +%Y%m%d%H%M%S)"
    echo -e "${YELLOW}Backing up existing rules file to $BACKUP_FILE${NC}"
    cp "$UDEV_RULES_FILE" "$BACKUP_FILE"
fi

# Create new rules file with header
echo -e "${YELLOW}Creating/updating udev rules file at $UDEV_RULES_FILE${NC}"
echo "# Voiture-Autonome Project Device Rules" > "$UDEV_RULES_FILE"
echo "# Created: $(date)" >> "$UDEV_RULES_FILE"
echo "# These rules create persistent device symlinks for Arduino and LiDAR sensors" >> "$UDEV_RULES_FILE"
echo "" >> "$UDEV_RULES_FILE"

# Add Arduino rule
echo -e "${GREEN}Adding Arduino rule to $UDEV_RULES_FILE${NC}"
echo -e $ARDUINO_RULE >> "$UDEV_RULES_FILE"
echo "" >> "$UDEV_RULES_FILE"

# Add USB rule
echo -e "${GREEN}Adding LiDAR sensor rule to $UDEV_RULES_FILE${NC}"
echo -e $USB_RULE >> "$UDEV_RULES_FILE"

# Verifying if the file exists and has content
if [ -f "$UDEV_RULES_FILE" ] && [ -s "$UDEV_RULES_FILE" ]; then
    echo -e "${GREEN}✓ udev rules file successfully configured${NC}"
else
    echo -e "${RED}× Failed to create or update udev rules file!${NC}"
    exit 1
fi

# Applying the rules
echo -e "${YELLOW}Reloading udev rules...${NC}"
udevadm control --reload-rules
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Rules loaded successfully${NC}"
else
    echo -e "${RED}× Failed to reload rules${NC}"
    exit 1
fi

echo -e "${YELLOW}Triggering udev rules...${NC}"
udevadm trigger
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Rules triggered successfully${NC}"
else
    echo -e "${RED}× Failed to trigger rules${NC}"
    exit 1
fi

# Check for currently connected devices
detect_devices

echo -e "\n${BLUE}=========================================================${NC}"
echo -e "${GREEN}✓ Configuration complete!${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Display verification instructions
echo -e "\n${YELLOW}To verify the setup:${NC}"

if [ "$ARDUINO_DETECTED" -eq 1 ]; then
    echo -e "1. Arduino should now be accessible at: ${GREEN}/dev/ttyACM${NC}"
    echo -e "   Run: ls -la /dev/ttyACM"
else
    echo -e "1. When you connect your Arduino, it will be accessible at: ${GREEN}/dev/ttyACM${NC}"
    echo -e "   After connecting, run: ls -la /dev/ttyACM"
fi

if [ "$LIDAR_DETECTED" -eq 1 ]; then
    echo -e "2. LiDAR should now be accessible at: ${GREEN}/dev/ttyUSB${NC}"
    echo -e "   Run: ls -la /dev/ttyUSB"
else
    echo -e "2. When you connect your LiDAR sensor, it will be accessible at: ${GREEN}/dev/ttyUSB${NC}"
    echo -e "   After connecting, run: ls -la /dev/ttyUSB"
fi

echo -e "\n${YELLOW}Additional information:${NC}"
echo -e "• If devices were already connected before running this script,"
echo -e "  you may need to disconnect and reconnect them."
echo -e "• The rules grant access to members of the 'dialout' group."
echo -e "• If you encounter permission issues, make sure your user is in the 'dialout' group"
echo -e "  and you've logged out and back in after running this script."

exit 0