import os
import sys
import json
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 setup/launch_login.py <account_id>")
        print("Example: python3 setup/launch_login.py 01")
        return

    acct_id = sys.argv[1]
    # Ensure 2-digit format
    if len(acct_id) == 1:
        acct_id = f"0{acct_id}"

    config_path = f"configs/data_{acct_id}/config.json"
    
    if not os.path.exists(config_path):
        print(f"Error: Config not found at {config_path}")
        print("Did you run 'python3 setup/create_twins.py' first?")
        return

    with open(config_path, 'r') as f:
        conf = json.load(f)

    container_name = f"android_{acct_id}"
    data_dir = f"/teamspace/studios/this_studio/tiktok_data/data_{acct_id}"
    image_name = "redroid/redroid:11.0.0_ndk_magisk"

    print(f"[*] Preparing Login Session for Account {acct_id}...")

    # Pre-flight Check: Ensure Image Exists
    try:
        img_check = subprocess.run(
            f"sudo docker images -q {image_name}", 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL
        )
        if not img_check.stdout.strip():
            print(f"\n❌ ERROR: Docker Image '{image_name}' not found locally!")
            print("You must build it first by running:")
            print("   bash scripts/setup_cloud.sh")
            return
    except Exception:
        pass # If check fails, let the run command handle it, but the check is safer.
    
    # Cleanup previous instances
    print(f"[*] Stopping any existing container named {container_name}...")
    subprocess.run(f"sudo docker stop {container_name}", shell=True, stderr=subprocess.DEVNULL)
    subprocess.run(f"sudo docker rm {container_name}", shell=True, stderr=subprocess.DEVNULL)

    # Build the full command
    # Note: Use sudo for docker on Lightning AI/Linux
    cmd = [
        "sudo", "docker", "run", "-d", "--rm", "--privileged",
        "-p", "5555:5555",
        "-v", f"{data_dir}:/data",
        "--name", container_name,
        image_name,
        f"androidboot.redroid_mac_address={conf['mac_address']}",
        f"androidboot.redroid_model={conf['model']}",
        "androidboot.redroid_native_bridge=1",
        "androidboot.redroid_gpu_mode=guest"
    ]

    print(f"[*] Launching Container...")
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ Container '{container_name}' is UP!")
        print("-" * 50)
        print("NEXT STEPS (Manual Login):")
        print(f"1. Start Tunnel: ./playit")
        print(f"   (Click the 'Claim URL' standard output link)")
        print(f"   (Create a 'Custom TCP Tunnel' to 127.0.0.1:5555)")
        print(f"2. On your LOCAL PC, connect via Scrcpy:")
        print(f"   adb connect <your-playit-address>")
        print(f"   scrcpy -s <your-playit-address>")
        print(f"3. Login to TikTok manually.")
        print(f"4. Once done, stop the container: sudo docker stop {container_name}")
        print("-" * 50)
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to launch container: {e}")

if __name__ == "__main__":
    main()
