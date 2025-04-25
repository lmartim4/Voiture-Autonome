#!/bin/bash

# Colors for messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[38;5;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Configuring system to recognize:${NC}"
echo -e "  • Arduino Nano 33 BLE (or similar) - will be mapped to /dev/ttyACM"
echo -e "  • LiDAR sensor (using CP210x bridge) - will be mapped to /dev/ttyUSB"
echo ""

if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}This script needs to be run as root (sudo)!${NC}"
    echo -e "${YELLOW}Please run: sudo $0${NC}"
    exit 1
fi

UDEV_RULES_FILE="/etc/udev/rules.d/99-voiture-autonome.rules"

ARDUINO_RULE="# Arduino Nano 33 BLE (vendor: 2341, product: 8057)\nSUBSYSTEM==\"tty\", ATTRS{idVendor}==\"2341\", ATTRS{idProduct}==\"8057\", SYMLINK+=\"ttyACM\", GROUP=\"dialout\", MODE=\"0666\""
USB_RULE="# LiDAR sensor with Silicon Labs CP210x USB to UART bridge (vendor: 10c4, product: ea60)\nSUBSYSTEM==\"tty\", ATTRS{idVendor}==\"10c4\", ATTRS{idProduct}==\"ea60\", SYMLINK+=\"ttyUSB\", GROUP=\"dialout\", MODE=\"0666\""

if [ ! -d "/etc/udev/rules.d" ]; then
    echo -e "${YELLOW}Creating directory /etc/udev/rules.d${NC}"
    mkdir -p /etc/udev/rules.d
fi

# Check if rules already exist
if [ -f "$UDEV_RULES_FILE" ]; then
    echo -e "${YELLOW}Detected existing udev rules file at $UDEV_RULES_FILE${NC}"
    
    # Check for Arduino rule
    if grep -q "ATTRS{idVendor}==\"2341\"" "$UDEV_RULES_FILE"; then
        echo -e "${YELLOW}• Arduino rule already exists${NC}"
        ARDUINO_EXISTS=1
    else
        ARDUINO_EXISTS=0
    fi
    
    # Check for LiDAR rule
    if grep -q "ATTRS{idVendor}==\"10c4\"" "$UDEV_RULES_FILE"; then
        echo -e "${YELLOW}• LiDAR rule already exists${NC}"
        LIDAR_EXISTS=1
    else
        LIDAR_EXISTS=0
    fi
    
    if [ "$ARDUINO_EXISTS" -eq 1 ] && [ "$LIDAR_EXISTS" -eq 1 ]; then
        echo -e "${YELLOW}All device rules are already configured.${NC}"
        echo -e "${YELLOW}Existing rules will be overwritten to ensure proper configuration.${NC}"
    fi
else
    echo -e "${GREEN}No existing udev rules file found. Creating new configuration.${NC}"
fi

detect_devices() {
    echo -e "\n${BLUE}Detecting currently connected devices...${NC}"

    if lsusb | grep -q "2341:8057"; then
        echo -e "${GREEN}✓ Arduino device detected (VendorID:ProductID - 2341:8057)${NC}"
        ARDUINO_DETECTED=1
    else
        echo -e "${YELLOW}× No Arduino device currently connected${NC}"
        ARDUINO_DETECTED=0
    fi
    
    if lsusb | grep -q "10c4:ea60"; then
        echo -e "${GREEN}✓ LiDAR device detected (VendorID:ProductID - 10c4:ea60)${NC}"
        LIDAR_DETECTED=1
    else
        echo -e "${YELLOW}× No LiDAR device currently connected${NC}"
        LIDAR_DETECTED=0
    fi
}

echo -e "${YELLOW}Creating/updating udev rules file at $UDEV_RULES_FILE${NC}"
echo "# Voiture-Autonome Project Device Rules" > "$UDEV_RULES_FILE"
echo "# Created: $(date)" >> "$UDEV_RULES_FILE"
echo "# These rules create persistent device symlinks for Arduino and LiDAR sensors" >> "$UDEV_RULES_FILE"
echo "" >> "$UDEV_RULES_FILE"

echo -e "${GREEN}Adding Arduino rule to $UDEV_RULES_FILE${NC}"
echo -e $ARDUINO_RULE >> "$UDEV_RULES_FILE"
echo "" >> "$UDEV_RULES_FILE"

echo -e "${GREEN}Adding LiDAR sensor rule to $UDEV_RULES_FILE${NC}"
echo -e $USB_RULE >> "$UDEV_RULES_FILE"

if [ -f "$UDEV_RULES_FILE" ] && [ -s "$UDEV_RULES_FILE" ]; then
    echo -e "${GREEN}✓ udev rules file successfully configured${NC}"
else
    echo -e "${RED}× Failed to create or update udev rules file!${NC}"
    exit 1
fi

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

detect_devices

echo -e "\n${GREEN}✓ Configuration complete!${NC}"
echo -e "\n${YELLOW}Verifying setup:${NC}"

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

echo -e "\n• If devices were already connected before running this script,"
echo -e "  you may need to disconnect and reconnect them."

exit 0