#!/bin/bash
set -e

echo "--- Setting up Cloud Environment ---"

# Ensure non-interactive apt
export DEBIAN_FRONTEND=noninteractive

# 1. Fix Docker Conflict & Install Dependencies
echo "[*] Checking Docker..."

# If docker command exists, skip installation to avoid conflicts
if command -v docker &> /dev/null; then
    echo "✅ Docker is already installed. Skipping install."
else
    echo "⚠️ Docker not found. Resolving conflicts and installing..."
    # CRITICAL FIX: Remove conflicting packages
    sudo apt-get remove -y containerd runc docker.io || true
    
    sudo apt-get update -y
    sudo apt-get install -y -o Dpkg::Options::="--force-confold" --fix-broken docker.io
fi

# Install other tools (ADB, Python, etc.)
echo "[*] Installing ADB and build tools..."
sudo apt-get install -y -o Dpkg::Options::="--force-confold" --fix-broken \
    android-tools-adb git python3 python3-pip lzip curl

# Install Playit.gg (Tunneling alternative to Ngrok)
echo "[*] Installing Playit.gg..."
if [ ! -f "playit" ]; then
    curl -SSL https://github.com/playit-cloud/playit-agent/releases/download/v0.15.26/playit-linux-amd64 -o playit
    chmod +x playit
fi

# Start Docker Service (Just in case it's stopped)
sudo service docker start || true

echo "--- Environment Ready. Starting Redroid Build... ---"

# Check if image already exists to save time
if [[ "$(sudo docker images -q redroid/redroid:11.0.0_ndk_magisk 2> /dev/null)" == "" ]]; then
    if [ ! -d "redroid-script" ]; then
        echo "[*] Cloning redroid-script..."
        git clone https://github.com/ayasa520/redroid-script.git
    fi
    
    echo "[*] Installing Python dependencies..."
    pip3 install -r redroid-script/requirements.txt
    
    echo "[*] Building Redroid Image..."
    # -a 11.0.0 : Android 11
    # -n        : Native Bridge (ARM support)
    # -m        : Magisk (Root)
    sudo python3 redroid-script/redroid.py -a 11.0.0 -n -m
    
    echo "[*] Cleaning up..."
    sudo rm -rf redroid-script
else
    echo "✅ Redroid image already exists. Skipping build."
fi

echo "SUCCESS: Redroid Environment Finalized."
