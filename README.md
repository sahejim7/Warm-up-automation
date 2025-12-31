# TikTok Automation Farm - Deployment Checklist

This guide serves as a checklist for deployment on Lightning AI (or compatible Linux/Docker environments).

## 1. Clone Repository
Get the code onto your machine.
```bash
git clone <your-repo-url>
cd <repo-name>
```

## 2. Setup Environment
This script will install Docker, ADB, Playit.gg, and build the custom Redroid image.
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
   The controller uses the `MODAL_URL` environment variable. Add it to your `.bashrc` or run:
   ```bash
   export MODAL_URL="<your_modal_url>"
   ```

## 5. Manual Login ("The Pain Phase")
You must manually log in to TikTok for each of the 20 accounts *once* to save the session tokens. We use **Playit.gg** for tunneling.

**The Loop (Repeat for accounts 01-20):**

1. **Launch Account Container**:
   ```bash
   python3 setup/launch_login.py 01
   ```
   *(Replace 01 with the account ID you are setting up)*

2. **Start Tunnel**:
   Run Playit in your terminal:
   ```bash
   ./playit
   ```
   - Click the **Claim URL** link printed in the terminal.
   - On the website: Create a **Custom TCP Tunnel** pointing to `127.0.0.1:5555`.
   - Copy the generated address (e.g., `purple-lion.ply.gg:12345`).

3. **Connect from your LOCAL PC**:
   - Install `scrcpy` and `adb` on your local machine if you haven't.
   - Run the following on your **Laptop/Desktop**:
   ```bash
   adb connect purple-lion.ply.gg:12345
   scrcpy -s purple-lion.ply.gg:12345
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
- **Playit Permission**: If `./playit` says permission denied, run `chmod +x playit`.
