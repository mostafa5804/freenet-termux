#!/data/data/com.termux/files/usr/bin/bash

echo "🔧 نصب وابستگی‌ها..."
pkg update -y
pkg install -y python git

echo "📦 نصب کتابخانه‌های مورد نیاز..."
pip install --upgrade pip
pip install requests

echo "✅ اجرا..."
python freenet_cli.py --count 30
