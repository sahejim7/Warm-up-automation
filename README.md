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
You must manually log in to TikTok for each of the 20 accounts *once* to save the session tokens.

**The Loop (Repeat for accounts 01-20):**

1. **Launch Account Container**:
   Instead of complex docker commands, use the helper:
   ```bash
   python3 setup/launch_login.py 01
   ```
   *(Replace 01 with the account ID you are setting up)*

2. **Tunnel with Ngrok**:
   ```bash
   ngrok tcp 5555
   ```

3. **Connect from your LOCAL PC**:
   - Install `scrcpy` on your local machine if you haven't.
   - Run the following (replacing the URL with the one ngrok gave you):
   ```bash
   adb connect 0.tcp.ngrok.io:XXXXX
   scrcpy -s 0.tcp.ngrok.io:XXXXX
   ```

4. **Login**: Perform the Login/Captcha inside the Scrcpy window.
5. **Cleanup**: Stop the container on the cloud when finished:
   ```bash
   sudo docker stop android_01
   ```

## 6. Run the Farm
Once all accounts are logged in, start the automation controller.
```bash
python3 farm/controller.py
```

## Troubleshooting
- **Apt Errors**: If `setup_cloud.sh` fails, run `sudo apt --fix-broken install`.
- **Docker Permission**: If you see "permission denied", ensure you are using `sudo` or your user is in the `docker` group.
