import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_file_download(url, click_class=""):
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
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        try:
            triggered = False

            # 1. Click by given class
            if isinstance(click_class, str) and click_class.strip() != "":
                try:
                    page.wait_for_selector(f'.{click_class}', timeout=5000)
                    page.click(f'.{click_class}')
                    print(f"[🖱️] Clicked element with class '{click_class}'")
                    triggered = True
                except Exception as e:
                    print(f"[⚠️] Could not click class '{click_class}': {e}")

            # 2. Default download selectors
            if not triggered:
                try:
                    download_selector = 'a[href$=".pdf"], a[download], button:has-text("Download")'
                    page.wait_for_selector(download_selector, timeout=5000)
                    page.click(download_selector)
                    print("[⬇️] Download triggered by default selector.")
                    triggered = True
                except Exception as e:
                    print(f"[⚠️] Default selector failed: {e}")

            # 3. Try by class or id that contains "download"
            if not triggered:
                try:
                    selector = '[class*="download" i], [id*="download" i]'
                    page.wait_for_selector(selector, timeout=10000, state="attached")
                    page.click(selector)
                    print("[🔍] Download triggered by 'download' in class or ID.")
                    triggered = True
                except Exception as e:
                    print(f"[⚠️] Fallback selector failed: {e}")

            if not triggered:
                print(f"[❌] No download trigger found.")

            time.sleep(7)

        except Exception as e:
            print(f"[❌] Failed to trigger download: {e}")
        finally:
            browser.close()

    tshark_proc.wait()
    print(f"✅ Download capture done: {pcap_file}")

def sniff_all_downloads():
    links = load_links_from_excel("Download")
    for url, click_class in links:
        sniff_file_download(url, click_class)
