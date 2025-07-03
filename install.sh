#!/data/data/com.termux/files/usr/bin/bash

echo "📦 نصب پیش‌نیازها..."
pkg update -y
pkg install -y python git termux-api

pip install --upgrade pip
pip install requests colorama qrcode

termux-setup-storage

echo "🚀 اجرای FreeNet Advanced..."
python freenet_advanced.py
