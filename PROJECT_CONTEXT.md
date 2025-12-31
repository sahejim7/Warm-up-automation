# Project: TikTok God Mode Farm (Hybrid Architecture)

## 1. Mission
Build a lightweight, scalable automation farm for 20 TikTok accounts using a "Digital Twin" strategy.
The system must run on $0 infrastructure, relying on "Ephemeral Compute" (Lightning AI) for the phones and "Serverless GPU" (Modal) for the intelligence.

## 2. Architecture Stack
*   **The Brain (AI):** Modal.com hosting `Magma-R1-4B` (Vision-Language Model). Exposes an HTTP API.
*   **The Body (Compute):** Lightning AI (CPU Studio) running Docker.
*   **The OS:** `redroid/redroid:11.0.0-latest` (Android 11).
*   **The Network:** Webshare SOCKS5 Proxies + Postern (Android App) for routing.
*   **State Management:** JSON Config files + Persistent Docker Volumes (`/data`). NO Databases.

## 3. Directory Structure
/tiktok-farm
  ├── brain/
  │   └── inference.py      # Modal app logic (Magma-R1)
  ├── farm/
  │   └── controller.py     # Main automation loop (The Farm Script)
  ├── setup/
  │   └── create_twins.py   # One-time script to generate config profiles
  ├── configs/              # Generated JSON profiles live here (GitIgnore this)
  └── requirements.txt      # Python dependencies

## 4. Critical Constraints (Do Not Violate)
1.  **No Databases:** State must be stored in flat `.json` files in `configs/`.
2.  **Sequential Execution:** We run 1 container at a time to save CPU. Wake -> Act -> Sleep -> Next.
3.  **Safety & Stealth (Mandatory):**
    *   **Timezone:** Must match the Proxy location (set via ADB property).
    *   **Battery:** Must be randomized (Level 40-90%, Discharging status) on every boot.
    *   **Hardware:** MAC Address and Device Model must be injected via Docker arguments.
    *   **Sensors:** Must be disabled or mocked to avoid returning (0,0,0).
4.  **Network:** Container must use Host Networking or Port Mapping, but traffic MUST route through the Proxy defined in the config.

## 5. Operational Workflow
1.  **Setup:** Run `create_twins.py` to generate 20 static profiles (MAC, Model, Proxy).
2.  **Deployment:** Deploy `brain/inference.py` to Modal to get the API URL.
3.  **Daily Run:** Run `farm/controller.py`. It loops through accounts 01-20, spinning up the Docker container with the specific profile, interacting via ADB + AI, then tearing it down.