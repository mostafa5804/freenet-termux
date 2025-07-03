#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Installing requirements..."
pkg update -y
pkg install -y python git termux-api

pip install --upgrade pip
pip install requests colorama qrcode

termux-setup-storage

echo "🚀 Running FreeNet..."
python freenet_cli.py
