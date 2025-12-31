import subprocess
import time
import json
import base64
import requests
import random
import re
import os

# Configuration
MODAL_URL = "PLACEHOLDER_URL"  # User will update this after deployment
DATA_DIR = "/teamspace/studios/this_studio/tiktok_data"
IMAGE_NAME = "redroid/redroid:11.0.0-native-bridge-magisk"

def execute_adb(cmd):
    """Executes an ADB command and returns the output."""
    full_cmd = f"adb -s localhost:5555 {cmd}"
    try:
        result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT)
        return result.decode('utf-8').strip()
    except subprocess.CalledProcessError as e:
        print(f"ADB Error: {e.output.decode('utf-8')}")
        return ""

def parse_magma_response(text):
    """Clean and parse JSON from the LLM response."""
    try:
        # Simple extraction if the LLM wraps code in markdown blocks
        match = re.search(r'```json\n(.*?)\n```', text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            json_str = text
        return json.loads(json_str)
    except Exception as e:
        print(f"Failed to parse Magma response: {e}")
        return None

def run_account(acct_id):
    print(f"[*] Starting session for Account {acct_id}")
    
    # Load config
    config_path = f"configs/data_{acct_id}/config.json"
    if not os.path.exists(config_path):
        print(f"Config not found for {acct_id}, skipping.")
        return

    with open(config_path, 'r') as f:
        conf = json.load(f)

    # 1. Docker Launch
    container_name = f"android_{acct_id}"
    
    # Construct Docker command
    docker_cmd = [
        "docker", "run", "-d", "--rm", "--privileged",
        "-p", "5555:5555",
        "-v", f"{DATA_DIR}/data_{acct_id}:/data",
        "--name", container_name,
        IMAGE_NAME,
        f"androidboot.redroid_mac_address={conf['mac_address']}",
        f"androidboot.redroid_model={conf['model']}",
        "androidboot.redroid_native_bridge=1",
        "androidboot.redroid_gpu_mode=guest"
    ]
    
    print(f"Launching container: {container_name}")
    try:
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError:
        print("Failed to start Docker container.")
        return

    # Wait for container to initialize
    print("Waiting for boot...")
    time.sleep(15) # Give generic boot time before adb connect

    # 2. ADB Init
    print("Connecting ADB...")
    subprocess.run("adb connect localhost:5555", shell=True)
    time.sleep(5)

    # 3. Stealth Setup
    print("Applying stealth settings...")
    # Timezone
    execute_adb(f"shell setprop persist.sys.timezone {conf['timezone']}")
    
    # Spoof Battery
    level = random.randint(40, 90)
    status = 3 # Discharging
    execute_adb("shell dumpsys battery set level " + str(level))
    execute_adb("shell dumpsys battery set status " + str(status))

    # 4. The Loop (20 mins)
    start_time = time.time()
    duration = 20 * 60 # 20 minutes
    
    print("Entering Main Loop...")
    while time.time() - start_time < duration:
        try:
            # Take Screenshot
            subprocess.run("adb -s localhost:5555 shell screencap -p > screen.png", shell=True)
            
            # Read and encode
            if os.path.exists("screen.png"):
                with open("screen.png", "rb") as image_file:
                    b64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
                # Send to MODAL
                payload = {
                    "image": b64_image,
                    "prompt": "You are a TikTok user. If ad, swipe up. If video is interesting, watch 10s then swipe. Output JSON."
                }
                
                if MODAL_URL != "PLACEHOLDER_URL":
                    response = requests.post(MODAL_URL + "/analyze", json=payload)
                    if response.status_code == 200:
                        action_data = parse_magma_response(response.json())
                        print(f"AI Decision: {action_data}")
                        
                        # Execute Action
                        if action_data:
                            action = action_data.get("action", "swipe_up")
                            
                            if action == "swipe_up":
                                # Add random noise to swipe
                                x1 = 540 + random.randint(-20, 20)
                                y1 = 1500 + random.randint(-50, 50)
                                x2 = 540 + random.randint(-20, 20)
                                y2 = 300 + random.randint(-50, 50)
                                duration_ms = random.randint(200, 400)
                                execute_adb(f"shell input swipe {x1} {y1} {x2} {y2} {duration_ms}")
                            elif action == "click":
                                # TODO: Implement specific click coordinates if AI provides them
                                pass
                            
                            # Watch delay if specified
                            if action_data.get("watch_duration"):
                                time.sleep(float(action_data["watch_duration"]))

            # Sleep random
            sleep_time = random.uniform(2, 5)
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"Error in loop: {e}")
            time.sleep(5)

    # 5. Teardown
    print("Tearing down container...")
    subprocess.run(f"docker stop {container_name}", shell=True)
    subprocess.run("adb disconnect localhost:5555", shell=True)
    if os.path.exists("screen.png"):
        os.remove("screen.png")
    print(f"Session for {acct_id} complete.")

if __name__ == "__main__":
    # Execution: Loop through accounts 01-20
    for i in range(1, 21):
        acct_id = f"{i:02d}"
        run_account(acct_id)
        
        # Brief pause between accounts
        time.sleep(5)
