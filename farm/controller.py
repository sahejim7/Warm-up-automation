import subprocess
import time
import json
import base64
import requests
import random
import re
import os
import sys

# Constants
# Try to get URL from Environment, otherwise use a placeholder/warning
MODAL_URL = os.getenv("MODAL_URL", "PLACEHOLDER_URL_SET_IN_ENV")

if MODAL_URL == "PLACEHOLDER_URL_SET_IN_ENV":
    print("⚠️ WARNING: MODAL_URL not set! Check your .env file or environment variables.")

# Standard Linux Path (Azure/Cloud compatible)
DATA_DIR = os.path.expanduser('~/tiktok_data')
IMAGE_NAME = "redroid/redroid:11.0.0_ndk_magisk"
ADB_PORT = "5555"
ADB_HOST = f"localhost:{ADB_PORT}"

def execute_adb(cmd):
    """Executes an ADB command strictly."""
    full_cmd = f"adb -s {ADB_HOST} {cmd}"
    try:
        # Using shell=True for flexibility with arguments, but be careful with inputs
        result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        # print(f"ADB Error ({cmd}): {e.output.decode('utf-8').strip()}")
        return None

def human_swipe(x1, y1, x2, y2):
    """
    Simulates a human-like swipe with randomization.
    Adds noise to coordinates and duration.
    """
    # Add noise to start and end points
    nx1 = x1 + random.randint(-10, 10)
    ny1 = y1 + random.randint(-10, 10)
    nx2 = x2 + random.randint(-10, 10)
    ny2 = y2 + random.randint(-10, 10)
    
    # Randomize duration
    duration = random.randint(200, 500)
    
    # Execute
    # "Curve it" implies we might want to do a multi-point swipe, but standard adb swipe is linear.
    execute_adb(f"shell input swipe {nx1} {ny1} {nx2} {ny2} {duration}")

def human_click(x, y):
    """
    Simulates a human-like tap.
    """
    nx = x + random.randint(-5, 5)
    ny = y + random.randint(-5, 5)
    execute_adb(f"shell input tap {nx} {ny}")

def get_screenshot():
    """
    Captures screenshot safely using exec-out to avoid line-ending corruption.
    Returns: base64 encoded string of the image.
    """
    try:
        # 'exec-out' writes binary data directly to stdout.
        cmd = ['adb', '-s', ADB_HOST, 'exec-out', 'screencap', '-p']
        image_data = subprocess.check_output(cmd)
        return base64.b64encode(image_data).decode('utf-8')
    except subprocess.CalledProcessError as e:
        print(f"Error getting screenshot: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error getting screenshot: {e}")
        return None

def run_account(acct_id):
    print(f"[*] Starting session for Account {acct_id}")
    
    # 1. Load Config
    config_path = f"configs/data_{acct_id}/config.json"
    if not os.path.exists(config_path):
        print(f"Config not found at {config_path}, skipping.")
        return

    try:
        with open(config_path, 'r') as f:
            conf = json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return

    # Ensure Data Directory Exists
    account_data_dir = os.path.join(DATA_DIR, f"data_{acct_id}")
    if not os.path.exists(account_data_dir):
        print(f"   Creating data directory: {account_data_dir}")
        os.makedirs(account_data_dir, exist_ok=True)

    # 2. Docker Start
    container_name = f"android_{acct_id}"
    print(f"   Launch container: {container_name}")
    
    # Cleanup previous instances just in case
    # Use sudo for Docker commands as requested
    subprocess.run(f"sudo docker stop {container_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(f"sudo docker rm {container_name}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    docker_cmd = (
        f"sudo docker run -d --rm --privileged "
        f"-p {ADB_PORT}:5555 "
        f"-v {account_data_dir}:/data "
        f"--name {container_name} "
        f"{IMAGE_NAME} "
        f"androidboot.redroid_mac_address={conf.get('mac_address', '02:00:00:00:00:00')} "
        f"androidboot.redroid_model={conf.get('model', 'Pixel 5')} "
        f"androidboot.redroid_native_bridge=1 "
        f"androidboot.redroid_gpu_mode=guest"
    )
    
    try:
        subprocess.run(docker_cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("   Failed to start Docker container.")
        return

    # 3. Connection Loop (Robust)
    print("   Connecting to ADB...")
    connected = False
    start_connect = time.time()
    while time.time() - start_connect < 30:
        # Try connecting
        res = subprocess.run(f"adb connect {ADB_HOST}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = res.stdout.decode('utf-8').strip()
        
        if "connected to" in output or "already connected" in output:
             # Verify device is actually listed as 'device' not 'offline'
             dev_list = subprocess.run("adb devices", shell=True, stdout=subprocess.PIPE).stdout.decode()
             if f"{ADB_HOST}\tdevice" in dev_list:
                 connected = True
                 print("   ADB Connected.")
                 break
        
        time.sleep(1)

    if not connected:
        print("   Failed to connect to ADB after 30s. Aborting.")
        subprocess.run(f"sudo docker stop {container_name}", shell=True)
        return

    # Wait for device system to be fully ready
    subprocess.run(f"adb -s {ADB_HOST} wait-for-device", shell=True)
    
    # 4. Stealth Injection
    print("   Applying stealth...")
    execute_adb(f"shell setprop persist.sys.timezone {conf.get('timezone', 'US/Pacific')}")
    
    # Battery
    level = random.randint(40, 90)
    execute_adb(f"shell dumpsys battery set level {level}")
    execute_adb("shell dumpsys battery set status 3") # Discharging
    
    # Disable sensors (optional) - skipping complex sensor hook for now, simple approach
    
    # 5. App Launch
    print("   Launching app...")
    # monkey -p PACKAGE ... launches the app
    execute_adb("shell monkey -p com.zhiliaoapp.musically -c android.intent.category.LAUNCHER 1")
    
    # 6. The AI Loop
    session_limit = 20 * 60 # 20 minutes
    loop_start = time.time()
    
    print("   Entering AI Loop...")
    while time.time() - loop_start < session_limit:
        try:
            # Get Screenshot
            b64_img = get_screenshot()
            
            if not b64_img:
                print("   Screenshot failed, retrying...")
                time.sleep(2)
                continue
            
            # API Call
            payload = {
                'image': b64_img,
                'prompt': (
                    "You are a TikTok user. "
                    "Analyze the UI. If it's an ad, output action='swipe_up'. "
                    "If interesting video, watch for 10s then swipe. "
                    "If there is a popup, click 'close' or 'not now'. "
                    "Output XML format: <answer>{\"action\": \"...\", \"bbox_2d\": [x1, y1, x2, y2]}</answer>"
                )
            }
            
            # Default fallback action
            action_performed = False
            
            if MODAL_URL and MODAL_URL != "placeholder" and MODAL_URL != "PLACEHOLDER_URL_SET_IN_ENV":
                try:
                    resp = requests.post(f"{MODAL_URL}/analyze", json=payload, timeout=10)
                    if resp.status_code == 200:
                        text_resp = resp.json() # Assuming modal returns string or json
                        if isinstance(text_resp, dict):
                            text_resp = json.dumps(text_resp)
                            
                        # Parse Magma Protocol
                        match = re.search(r'<answer>(.*?)</answer>', text_resp, re.DOTALL)
                        if match:
                            raw_json = match.group(1)
                            decision = json.loads(raw_json)
                            
                            act = decision.get("action", "swipe_up")
                            
                            if act == "swipe_up":
                                human_swipe(360, 1000, 360, 400)
                                action_performed = True
                            
                            elif act == "click":
                                bbox = decision.get("bbox_2d")
                                if bbox and len(bbox) == 4:
                                    cx = (bbox[0] + bbox[2]) // 2
                                    cy = (bbox[1] + bbox[3]) // 2
                                    human_click(cx, cy)
                                    action_performed = True
                        else:
                             print("   No <answer> tag found in response.")
                except Exception as api_err:
                    print(f"   API Error: {api_err}")

            # Fallback
            if not action_performed:
                print("   Fallback: Swiping up.")
                human_swipe(360, 1000, 360, 400)
            
            # Sleep (Behavioral)
            sleep_dur = random.uniform(3.0, 7.0)
            time.sleep(sleep_dur)
            
        except KeyboardInterrupt:
            print("   User interrupted.")
            break
        except Exception as e:
            print(f"   Loop error: {e}")
            time.sleep(2)

    # 7. Teardown
    print("   Tearing down...")
    subprocess.run(f"sudo docker stop {container_name}", shell=True, stdout=subprocess.DEVNULL)
    subprocess.run(f"sudo docker rm {container_name}", shell=True, stdout=subprocess.DEVNULL)
    print(f"[*] Account {acct_id} finished.")


if __name__ == "__main__":
    # Main: Loop accounts 01-20
    # Ensuring we run sequentially as we reuse port 5555
    print("Starting Main Farm Controller...")
    
    # Range 1 to 20 inclusive
    for i in range(1, 21):
        acct_id = f"{i:02d}"
        run_account(acct_id)
        
        # Small pause between accounts cleanup
        time.sleep(5)
