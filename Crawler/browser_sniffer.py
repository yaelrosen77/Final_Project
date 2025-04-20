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
    html_file = f"{out_dir}/{app_name}_html.html"

    print(f"\n🟢 Starting browsing capture for {app_name}...")

    # Start tshark for packet capture
    tshark_proc = subprocess.Popen(
        ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(1)  # Allow tshark to start before the browser

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see what happens
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Save the HTML content
            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"[📄] HTML saved to {html_file}")

            # Scroll and interact with the page
            for _ in range(3):
                page.mouse.wheel(0, 1000)
                time.sleep(1)
                page.mouse.wheel(0, -500)
                time.sleep(1)

            # Try clicking 2 internal or site-related links
            links = page.query_selector_all("a[href^='/'], a[href*='" + app_name.lower() + "']")
            for i in range(min(2, len(links))):
                try:
                    print(f"[🖱️] Clicking link {i+1}")
                    links[i].click(timeout=5000)
                    time.sleep(5)
                except:
                    continue

        except Exception as e:
            print(f"[❌] Browsing session failed: {e}")
        finally:
            browser.close()

    tshark_proc.wait()
    print(f"✅ Browsing capture done: {pcap_file}")

def sniff_all_browsing():
    links = load_links_from_excel("Browsing")[:5]
    for url, _ in links:
        sniff_browsing(url)
