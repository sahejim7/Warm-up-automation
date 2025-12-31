import os
import json
import random
import sys
import time
import requests

# Constants
DEFAULT_TIMEZONE = "America/New_York"
DEVICE_MODELS = [
    'Pixel 6', 
    'Pixel 7', 
    'Samsung S21', 
    'Samsung S22', 
    'OnePlus 9'
]

def generate_mac_address():
    """Generates a random valid MAC address."""
    mac = [0x02, 0x00, 0x00, 0x00, 0x00, 0x00] 
    for i in range(1, 6):
        mac[i] = random.randint(0x00, 0xff)
    return ':'.join(map(lambda x: "%02x" % x, mac))

def load_proxies(filepath):
    """Reads and parses proxies from file with | timezone override support."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Proxy file not found at: {filepath}")
    
    proxies = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            # Split timezone override
            tz_override = None
            if '|' in line:
                line, tz_override = line.split('|', 1)
            
            parts = line.split(':')
            if len(parts) == 4:
                proxies.append({
                    'ip': parts[0],
                    'port': parts[1],
                    'user': parts[2],
                    'pass': parts[3],
                    'timezone': tz_override
                })
    
    if not proxies:
        raise ValueError("No valid proxies found in proxies.txt")
    
    return proxies

def get_ip_timezone(ip):
    """Detects timezone for a given IP using ip-api.com."""
    try:
        url = f"http://ip-api.com/json/{ip}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                return data.get('timezone', DEFAULT_TIMEZONE)
    except Exception as e:
        print(f"Warning: Timezone detection failed for {ip}: {e}")
    
    return DEFAULT_TIMEZONE

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configs_dir = os.path.join(base_dir, "configs")
    proxies_path = os.path.join(base_dir, "proxies.txt")

    try:
        proxies = load_proxies(proxies_path)
        print(f"Loaded {len(proxies)} proxies.")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    if not os.path.exists(configs_dir):
        os.makedirs(configs_dir)

    print("Generating Digital Twins (Manual Timezone Override)...")
    print("-" * 60)

    for i in range(1, 21):
        account_id = f"{i:02d}"
        id_folder = os.path.join(configs_dir, f"data_{account_id}")
        
        if not os.path.exists(id_folder):
            os.makedirs(id_folder)

        config_path = os.path.join(id_folder, "config.json")
        
        # Round-robin proxy assignment
        proxy = proxies[(i - 1) % len(proxies)]
        
        # Logic: Manual Override > API > Fallback
        if proxy['timezone']:
            source = "User Override"
            final_tz = proxy['timezone']
        else:
            print(f"[{account_id}] ⚠️ Auto-detecting timezone (Less Accurate) for {proxy['ip']}...", end=" ", flush=True)
            source = "API Auto-detect"
            final_tz = get_ip_timezone(proxy['ip'])
            print(f"{final_tz}")
            time.sleep(1) # Rate limiting for API

        # Report to user
        print(f"[{account_id}] Proxy: {proxy['ip']} -> Timezone: {final_tz} ({source})")

        profile = {
            "account_id": account_id,
            "mac_address": generate_mac_address(),
            "model": random.choice(DEVICE_MODELS),
            "proxy_ip": proxy['ip'],
            "proxy_port": proxy['port'],
            "proxy_user": proxy['user'],
            "proxy_pass": proxy['pass'],
            "timezone": final_tz
        }

        with open(config_path, "w") as f:
            json.dump(profile, f, indent=4)
        
    print("\n" + "="*60)
    print("DONE! Profiles generated with Security-Hardened Timezones.")
    print("="*60)

if __name__ == "__main__":
    main()
