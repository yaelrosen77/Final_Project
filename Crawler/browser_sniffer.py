import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_browsing(url):
    app_name = get_app_name(url)
    out_dir = f"/app/browsing"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_browse.pcap"

    print(f"\n🟢 Starting browsing capture for {app_name}...")

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
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
                page.mouse.wheel(0, -500)
                time.sleep(1)

            links = page.query_selector_all("a[href^='/'], a[href*='" + get_app_name(url).lower() + "']")
            for i in range(min(2, len(links))):
                try:
                    links[i].click(timeout=5000)
                    time.sleep(5)
                except:
                    continue
        except Exception as e:
            print(f"Browsing session failed: {e}")

        browser.close()

    tshark_proc.wait()
    print(f"✅ Browsing capture done: {pcap_file}")

def sniff_all_browsing():
    links = load_links_from_excel("Browsing")
    for url, _ in links:
        sniff_browsing(url)
