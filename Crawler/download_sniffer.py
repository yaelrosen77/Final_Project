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
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, timeout=60000, wait_until="domcontentloaded")

        triggered = False
        previous_url = page.url

        def try_click(selector, label):
            nonlocal triggered
            try:
                page.wait_for_selector(selector, timeout=5000)
                page.click(selector)
                print(f"[🖱️] Clicked with selector ({label}): {selector}")
                triggered = True
            except Exception as e:
                print(f"[⚠️] {label} selector failed: {e}")

        # 1. Click by class name
        if play_class and not triggered:
            try_click(play_class, "class")

        # 2. Default selector
        if not triggered:
            try_click('a[href$=".pdf"], a[download], button:has-text("Download")', "Default")

        # 3. Fallback by class or id
        if not triggered:
            try_click('[class*="download" i], [id*="download" i]', "Fallback")

        time.sleep(2)  # זמן לדף לטעון מחדש או להחליף כתובת
        current_url = page.url

        if current_url != previous_url and current_url.lower().endswith(".pdf"):
            print(f"[🌍] Detected navigation to PDF: {current_url}")
            response = context.request.get(current_url)
            filename = os.path.basename(current_url).split("?")[0]
            save_path = os.path.join(out_dir, filename)
            with open(save_path, "wb") as f:
                f.write(response.body())
            print(f"[✅] PDF saved to: {save_path}")
        else:
            print("[❌] No PDF detected after interaction.")
        time.sleep(6)

        browser.close()
    tshark_proc.wait()
    print(f"✅ Sniffing complete: {pcap_file}")


def sniff_all_downloads():
    links = load_links_from_excel("Download")[3:]
    for url, play_class, pre_class in links:
        sniff_file_download(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_downloads()
