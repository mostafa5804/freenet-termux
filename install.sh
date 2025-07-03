#!/bin/bash

# --- ANSI Color Codes ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- شروع نصب Freenet برای Termux ---${NC}"

# 1. Update packages and install dependencies
echo -e "\n${YELLOW}مرحله ۱: به‌روزرسانی پکیج‌ها و نصب وابستگی‌ها...${NC}"
pkg update -y && pkg upgrade -y
pkg install -y python git unzip termux-api

# 2. Setup storage access
echo -e "\n${YELLOW}مرحله ۲: درخواست دسترسی به حافظه داخلی...${NC}"
termux-setup-storage
echo -e "${GREEN}دسترسی به حافظه باید تایید شود. اگر پنجره‌ای باز شد، 'Allow' را بزنید.${NC}"
sleep 3

# 3. Install Python requirements
echo -e "\n${YELLOW}مرحله ۳: نصب کتابخانه‌های پایتون...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    echo -e "${RED}خطا: فایل requirements.txt یافت نشد!${NC}"
    exit 1
fi

# 4. Download and set up Xray-core
echo -e "\n${YELLOW}مرحله ۴: دانلود و نصب Xray-core...${NC}"
# Find the latest release URL for linux-arm64-v8a
XRAY_LATEST_URL=$(curl -s "https://api.github.com/repos/XTLS/Xray-core/releases/latest" | grep "browser_download_url.*Xray-linux-arm64-v8a.zip" | cut -d : -f 2,3 | tr -d \")

if [ -z "$XRAY_LATEST_URL" ]; then
    echo -e "${RED}خطا: امکان یافتن لینک دانلود آخرین نسخه Xray وجود ندارد!${NC}"
    exit 1
fi

echo "در حال دانلود از: $XRAY_LATEST_URL"
curl -L -o xray.zip "$XRAY_LATEST_URL"

if [ $? -ne 0 ]; then
    echo -e "${RED}دانلود Xray با خطا مواجه شد.${NC}"
    exit 1
fi

echo "خارج کردن از حالت فشرده..."
unzip -o xray.zip xray
rm xray.zip
chmod +x xray

if [ -f "xray" ]; then
    echo -e "${GREEN}Xray-core با موفقیت نصب شد.${NC}"
else
    echo -e "${RED}نصب Xray با خطا مواجه شد.${NC}"
    exit 1
fi


# 5. Final instructions
echo -e "\n\n${GREEN}--- نصب با موفقیت به پایان رسید! ---${NC}"
echo -e "برای اجرای برنامه، دستور زیر را وارد کنید:"
echo -e "${YELLOW}python freenet_termux.py${NC}"
