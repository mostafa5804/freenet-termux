#!/bin/bash

# --- ANSI Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# --- Installation Directory ---
INSTALL_DIR="$HOME/freenet-termux"
REPO_URL="https://github.com/mostafa5804/freenet-termux.git"

echo -e "${GREEN}--- Starting Freenet for Termux Installation ---${NC}"

# 1. Update packages and install Git first
echo -e "\n${YELLOW}Step 1: Updating packages and installing Git...${NC}"
pkg update -y && pkg upgrade -y
pkg install -y git

# 2. Clone the repository
echo -e "\n${YELLOW}Step 2: Cloning the Freenet repository...${NC}"
if [ -d "$INSTALL_DIR" ]; then
    echo "An existing installation was found. Backing it up..."
    mv "$INSTALL_DIR" "$INSTALL_DIR-$(date +%s).bak"
fi
git clone "$REPO_URL" "$INSTALL_DIR"
cd "$INSTALL_DIR" || { echo -e "${RED}Failed to change directory to $INSTALL_DIR. Aborting.${NC}"; exit 1; }

# 3. Install other dependencies
echo -e "\n${YELLOW}Step 3: Installing dependencies (Python, Unzip, Termux-API)...${NC}"
pkg install -y python unzip termux-api

# 4. Setup storage access
echo -e "\n${YELLOW}Step 4: Requesting storage access...${NC}"
termux-setup-storage
echo -e "${GREEN}Please grant storage permission if a popup appears.${NC}"
sleep 3

# 5. Install Python requirements
echo -e "\n${YELLOW}Step 5: Installing Python libraries...${NC}"
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo -e "${RED}Error: requirements.txt not found! Aborting.${NC}"
    exit 1
fi

# 6. Download and set up Xray-core
echo -e "\n${YELLOW}Step 6: Downloading and setting up Xray-core...${NC}"
XRAY_LATEST_URL=$(curl -s "https://api.github.com/repos/XTLS/Xray-core/releases/latest" | grep "browser_download_url.*Xray-linux-arm64-v8a.zip" | cut -d : -f 2,3 | tr -d \")

if [ -z "$XRAY_LATEST_URL" ]; then
    echo -e "${RED}Error: Could not find the latest Xray-core download URL. Aborting.${NC}"
    exit 1
fi

echo "Downloading from: $XRAY_LATEST_URL"
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

# 7. Final instructions
echo -e "\n\n${GREEN}--- Installation Complete! ---${NC}"
echo -e "To run the application, use the following commands:"
echo -e "1. Change directory: ${YELLOW}cd $INSTALL_DIR${NC}"
echo -e "2. Run the script:   ${YELLOW}python freenet_termux.py${NC}"
