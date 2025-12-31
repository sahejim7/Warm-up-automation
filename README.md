# TikTok Automation Farm - Deployment Checklist

This guide serves as a checklist for deploying the automation farm on a Lightning AI studio (or similar Linux cloud environment).

## 1. Clone Repository
Get the code onto your machine.
```bash
git clone <your-repo-url>
cd <repo-name>
```

## 2. Setup Environment
This script will install Docker, ADB, and build the custom Redroid image required for the farm.
```bash
bash scripts/setup_cloud.sh
```

## 3. Deploy Brain (Modal)
Deploy the Magma-R1 inference engine to Modal.com to get your API endpoint.
```bash
pip install modal
modal setup  # Authenticate if needed
modal deploy brain/inference.py
```
**Action:** Copy the URL found in the terminal output (e.g., `https://workspace-name--magma-brain-analyze.modal.run`).

## 4. Configuration
1. **Proxies**: Create/Edit `proxies.txt` in the root. Format: `ip:port:user:pass:timezone` (one per line).
2. **Generate Twins**: Create the configuration files for your 20 accounts.
   ```bash
   python3 setup/create_twins.py
   ```
3. **Update Controller**:
   Open `farm/controller.py` and replace `MODAL_URL = "placeholder"` with your actual Modal URL from Step 3.

## 5. Manual Login ("The Pain Phase")
You must manually log in to TikTok for each of the 20 accounts *once* to save the session tokens in the persistent volume.

**Setup remote access:**
1. Install ngrok on the cloud instance:
   ```bash
   pip install pyngrok
   ngrok authtoken <YOUR_TOKEN>
   ```

**The Loop (Repeat for accounts 01-20):**
1. Start a specific container manually (you can look at `farm/controller.py` for the exact run command or use a temporary helper script).
   ```bash
   # Example for account 01
   docker run -d --rm --privileged -p 5555:5555 \
     -v /teamspace/studios/this_studio/tiktok_data/data_01:/data \
     --name android_01 \
     redroid/redroid:11.0.0-native-bridge-magisk \
     androidboot.redroid_mac_address=<MAC_FROM_CONFIG> \
     androidboot.redroid_model=<MODEL_FROM_CONFIG> \
     androidboot.redroid_native_bridge=1 \
     androidboot.redroid_gpu_mode=guest
   ```
2. Tunnel port 5555:
   ```bash
   ngrok tcp 5555
   ```
3. **On your LOCAL PC**:
   ```bash
   # Connect to the ngrok address (e.g., 0.tcp.ngrok.io:12345)
   adb connect 0.tcp.ngrok.io:12345
   scrcpy -s 0.tcp.ngrok.io:12345
   ```
4. Perform the Login/Captcha inside the Scrcpy window.
5. Stop the container on the cloud: `docker stop android_01`.

## 6. Run the Farm
Once all accounts are logged in, start the automation controller. It will loop through all 20 accounts sequentially.
```bash
python3 farm/controller.py
```
