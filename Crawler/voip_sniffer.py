import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from base_sniffer import BaseSniffer, get_app_name, load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_voip(url):
    app_name = get_app_name(url)
    out_dir = f"/app/voip"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_voip.pcap"

    print(f"\n🟢 Starting VOIP capture for {app_name}...")

    tshark_proc = subprocess.Popen(
        ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(permissions=["microphone", "camera"])
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        try:
            page.click("text=Start", timeout=5000)
            time.sleep(1)
            page.click("text=Call", timeout=5000)
            time.sleep(30)
            page.click("text=Hang up", timeout=5000)
        except Exception as e:
            print(f"VOIP session failed: {e}")

        browser.close()

    tshark_proc.wait()
    print(f"✅ VOIP capture done: {pcap_file}")

def sniff_all_voip():
    links = load_links_from_excel("VOIP")
    for url, _ in links:
        sniff_voip(url)
