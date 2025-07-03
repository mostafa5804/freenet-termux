#!/bin/bash

# --- ANSI Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# --- Configuration ---
INSTALL_DIR="$HOME/freenet-termux"
REPO_URL="https://github.com/mostafa5804/freenet-termux.git"

echo -e "${GREEN}--- Starting Freenet for Termux Installation ---${NC}"

# --- Step 1: Prepare Project Files ---
echo -e "\n${YELLOW}Step 1: Preparing project files...${NC}"
# Install git first, as it's needed for cloning
pkg install git -y

# Check if we are already inside a cloned repo. If not, clone it.
if [ ! -d ".git" ]; then
    echo "Cloning repository..."
    # Create the directory if it doesn't exist
    mkdir -p "$INSTALL_DIR"
    # Clone the repo into the directory
    git clone "$REPO_URL" "$INSTALL_DIR"
    # Change directory to the newly cloned repo
    cd "$INSTALL_DIR" || { echo -e "${RED}Failed to enter project directory. Aborting.${NC}"; exit 1; }
else
    echo "Already inside a cloned repository. Skipping clone."
fi


# --- Step 2: Install System Dependencies ---
echo -e "\n${YELLOW}Step 2: Installing system dependencies (Python, Unzip, Termux-API)...${NC}"
pkg install -y python unzip termux-api

# --- Step 3: Setup Storage Access ---
echo -e "\n${YELLOW}Step 3: Requesting storage access...${NC}"
termux-setup-storage
sleep 3

# --- Step 4: Install Python Libraries ---
echo -e "\n${YELLOW}Step 4: Installing Python libraries from local folder...${NC}"
if [ -f "requirements.txt" ] && [ -d "libs" ]; then
    pip install --no-index --find-links=./libs -r requirements.txt
else
    echo -e "${RED}Error: requirements.txt or libs/ folder not found! Aborting.${NC}"
    exit 1
fi

# --- Step 5: Setup Xray-core ---
echo -e "\n${YELLOW}Step 5: Setting up Xray-core from local archive...${NC}"
XRAY_ZIP_FILE="xray.zip"

if [ -f "$XRAY_ZIP_FILE" ]; then
    echo "Extracting local Xray archive (xray.zip)..."
    unzip -o "$XRAY_ZIP_FILE" xray
    chmod +x xray
    echo -e "${GREEN}Xray is ready.${NC}"
else
    echo -e "${RED}Error: $XRAY_ZIP_FILE not found! Aborting.${NC}"
    exit 1
fi

# --- Step 6: Final Instructions ---
echo -e "\n\n${GREEN}--- Installation Complete! ---${NC}"
echo -e "To run the application, make sure you are in the project directory:"
echo -e "${YELLOW}cd $INSTALL_DIR${NC}"
echo -e "Then run the command:"
echo -e "${YELLOW}python freenet_termux.py${NC}"
