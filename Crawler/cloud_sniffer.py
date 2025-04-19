import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_cloud_upload(url):
    app_name = get_app_name(url)
    out_dir = f"/app/cloud"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_upload.pcap"

    print(f"\n🟢 Starting cloud upload capture for {app_name}...")

    tshark_proc = subprocess.Popen(
        ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        try:
            fake_file = os.path.abspath("dummy_upload.txt")
            with open(fake_file, "w") as f:
                f.write("This is a dummy file.")

            input_selector = 'input[type="file"]'
            page.wait_for_selector(input_selector, timeout=10000)
            page.set_input_files(input_selector, fake_file)
            try:
                page.click('button[type="submit"], input[type="submit"]', timeout=5000)
            except:
                pass

            time.sleep(10)
            os.remove(fake_file)
        except Exception as e:
            print(f"Upload failed: {e}")

        browser.close()

    tshark_proc.wait()
    print(f"✅ Upload capture done: {pcap_file}")

def sniff_all_cloud():
    links = load_links_from_excel("Cloud")
    for url, _ in links:
        sniff_cloud_upload(url)
