import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_file_download(url):
    app_name = get_app_name(url)
    out_dir = f"/app/download"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_download.pcap"

    print(f"\n🟢 Starting download capture for {app_name}...")

    tshark_proc = subprocess.Popen(
        ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        try:
            download_selector = 'a[href$=".pdf"], a[download], button:has-text("Download")'
            page.wait_for_selector(download_selector, timeout=10000)
            page.click(download_selector)
            print("Download triggered.")
            time.sleep(7)
        except Exception as e:
            print(f"Failed to trigger download: {e}")

        browser.close()

    tshark_proc.wait()
    print(f"✅ Download capture done: {pcap_file}")

def sniff_all_downloads():
    links = load_links_from_excel("Download")
    for url, _ in links:
        sniff_file_download(url)
