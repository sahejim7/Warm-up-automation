#!/bin/bash
set -e

echo "[*] Updating apt and installing dependencies..."
sudo apt-get update
sudo apt-get install -y docker.io android-tools-adb git python3 python3-pip lzip

echo "[*] Cloning redroid-script..."
git clone https://github.com/ayasa520/redroid-script.git

echo "[*] Installing Python dependencies..."
pip3 install -r redroid-script/requirements.txt

echo "[*] Building Redroid Image..."
# -a 11.0.0 : Android 11
# -n        : Native Bridge (ARM support)
# -m        : Magisk (Root)
sudo python3 redroid-script/redroid.py -a 11.0.0 -n -m

echo "[*] Cleaning up..."
rm -rf redroid-script

echo "SUCCESS: Redroid Image Built: redroid/redroid:11.0.0-native-bridge-magisk"
