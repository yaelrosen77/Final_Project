import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_file_download(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/download"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_download.pcap"

    print(f"\n🟢 Starting download capture for {app_name}...")

    # Start tshark
    tshark_proc = subprocess.Popen(
        ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # Get list of files BEFORE clicking
        existing_files = set(os.listdir(out_dir))

        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        triggered = False

        def try_click(selector, label):
            nonlocal triggered
            try:
                elements = page.query_selector_all(selector)
                for el in elements:
                    try:
                        el.click(force=True)
                        print(f"[🖱️] Clicked one of ({label}) matches: {selector}")
                        time.sleep(1.5)
                        triggered = True
                        break
                    except Exception:
                        continue
                if not triggered:
                    print(f"[⚠️] No clickable element found for ({label}): {selector}")
            except Exception as e:
                print(f"[⚠️] {label} selector failed: {e}")

        # Try clicking in order
        if play_class and not triggered:
            selector = play_class.strip()
            if not selector.startswith(".") and not selector.startswith("#") and " " not in selector:
                selector = f".{selector}"
            try_click(selector, "class")

        if not triggered:
            try_click('a[href$=".pdf"], a[download], button:has-text("Download")', "Default")

        if not triggered:
            try_click('[class*="download" i], [id*="download" i]', "Fallback")

        # Wait for the file to be written
        print("⏳ Waiting for file to be written...")
        time.sleep(10)

        # Check for new files
        new_files = set(os.listdir(out_dir)) - existing_files
        if new_files:
            for file in new_files:
                print(f"[✅] File detected in folder: {file}")
        else:
            print("[❌] No file was downloaded or detected in folder.")

        browser.close()

    tshark_proc.wait()
    print(f"✅ Sniffing complete: {pcap_file}")

def sniff_all_downloads():
    links = load_links_from_excel("Download")[53:]
    for url, play_class, pre_class in links:
        sniff_file_download(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_downloads()
