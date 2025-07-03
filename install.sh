#!/bin/bash

# --- ANSI Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}--- Starting Freenet for Termux Installation ---${NC}"

# 1. Update packages and install dependencies
echo -e "\n${YELLOW}Step 1: Installing system dependencies (Python, Unzip, Termux-API)...${NC}"
pkg install -y python unzip termux-api

# 2. Setup storage access
echo -e "\n${YELLOW}Step 2: Requesting storage access...${NC}"
termux-setup-storage
sleep 3

# 3. Install Python requirements from local libs
echo -e "\n${YELLOW}Step 3: Installing Python libraries from local folder...${NC}"
if [ -f "requirements.txt" ] && [ -d "libs" ]; then
    pip install --no-index --find-links=./libs -r requirements.txt
else
    echo -e "${RED}Error: requirements.txt or libs/ folder not found! Aborting.${NC}"
    exit 1
fi

# 4. Set up Xray-core from local file
echo -e "\n${YELLOW}Step 4: Setting up Xray-core from local file...${NC}"
if [ -f "xray" ]; then
    chmod +x ./xray
    echo -e "${GREEN}Xray is ready.${NC}"
else
    echo -e "${RED}Error: Xray executable not found! Aborting.${NC}"
    exit 1
fi

# 5. Final instructions
echo -e "\n\n${GREEN}--- Installation Complete! ---${NC}"
echo -e "To run the application, use the command:"
echo -e "${YELLOW}python freenet_termux.py${NC}"
