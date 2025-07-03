#!/bin/bash

# --- ANSI Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}--- Starting Freenet for Termux Installation ---${NC}"

# 1. Update packages and install dependencies
echo -e "\n${YELLOW}Step 1: Installing system dependencies (Python, Unzip, Curl, Termux-API)...${NC}"
pkg install -y python unzip curl termux-api

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

# 4. Download and set up Xray-core from official source
echo -e "\n${YELLOW}Step 4: Downloading and setting up Xray-core...${NC}"
# Find and download the latest Xray-core for arm64
XRAY_LATEST_URL=$(curl -s "https://api.github.com/repos/XTLS/Xray-core/releases/latest" | grep "browser_download_url.*Xray-linux-arm64-v8a.zip" | cut -d : -f 2,3 | tr -d \")

if [ -z "$XRAY_LATEST_URL" ]; then
    echo -e "${RED}Error: Could not find the latest Xray-core download URL. Aborting.${NC}"
    exit 1
fi

echo "Downloading Xray from official source..."
curl -L -o xray.zip "$XRAY_LATEST_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to download Xray-core.${NC}"
    exit 1
fi

echo "Extracting xray..."
unzip -o xray.zip xray
rm xray.zip
chmod +x xray

if [ -f "xray" ]; then
    echo -e "${GREEN}Xray-core installed successfully.${NC}"
else
    echo -e "${RED}Failed to install Xray-core.${NC}"
    exit 1
fi


# 5. Final instructions
echo -e "\n\n${GREEN}--- Installation Complete! ---${NC}"
echo -e "To run the application, use the command:"
echo -e "${YELLOW}python freenet_termux.py${NC}"
