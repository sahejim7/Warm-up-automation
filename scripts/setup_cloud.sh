#!/bin/bash
set -e

echo "--- Setting up Cloud Environment ---"

# 1. Fix Docker Conflict & Install Dependencies
echo "[*] Checking Docker..."

# If docker command exists, skip installation to avoid conflicts
if command -v docker &> /dev/null; then
    echo "✅ Docker is already installed. Skipping install."
else
    echo "⚠️ Docker not found. Resolving conflicts and installing..."
    # CRITICAL FIX: Remove the conflicting package first
    sudo apt-get remove -y containerd runc || true
    
    sudo apt-get update
    sudo apt-get install -y docker.io
fi

# Install other tools (ADB, Python, etc.)
echo "[*] Installing ADB and build tools..."
sudo apt-get install -y android-tools-adb git python3 python3-pip lzip

# Start Docker Service (Just in case it's stopped)
sudo service docker start || true

echo "--- Environment Ready. Starting Redroid Build... ---"

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
