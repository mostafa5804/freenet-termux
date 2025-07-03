#!/data/data/com.termux/files/usr/bin/bash

echo "📦 نصب پیش‌نیازها..."
pkg update -y
pkg install -y python git termux-api

pip install --upgrade pip
pip install requests colorama qrcode

termux-setup-storage

# --- این بخش باید اضافه شود ---
echo "⏬ در حال دانلود اسکریپت اصلی..."
curl -sLO https://raw.githubusercontent.com/mostafa5804/freenet-termux-advanced/main/freenet_advanced.py

echo "🚀 اجرای FreeNet Advanced..."
python freenet_advanced.py
