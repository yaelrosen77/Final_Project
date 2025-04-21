import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from utils import get_app_name
from excel_loader import load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
def sniff_cloud_upload(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/cloud"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_upload.pcap"
    html_file = f"{out_dir}/{app_name}_html.html"

    print(f"\n🟢 Starting cloud upload capture for {app_name}...")

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

        try:
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"[📄] HTML saved to {html_file}")

            fake_file = os.path.abspath("dummy_upload.txt")
            with open(fake_file, "w") as f:
                f.write("This is a dummy file.")

            input_selector = 'input[type="file"]'
            page.wait_for_selector(input_selector, timeout=10000, state="attached")
            page.set_input_files(input_selector, fake_file)
            print(f"[📤] File uploaded using {input_selector}")

            try:
                submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
                if submit_btn:
                    submit_btn.click()
                    print("[🖱️] Clicked submit button.")
            except:
                print("[ℹ️] No clickable submit button found.")

            # ← כאן התנאי המתוקן: רק אם play_class לא ריק
            if isinstance(play_class, str) and play_class.strip() != '':
                try:
                    class_btn = page.query_selector(f'.{play_class}')
                    if class_btn:
                        class_btn.click()
                        print(f"[🖱️] Clicked button with class: {play_class}")
                    else:
                        print(f"[ℹ️] No button found with class: {play_class}")
                except Exception as e:
                    print(f"[⚠️] Failed to click class button: {e}")

            time.sleep(4)
            os.remove(fake_file)

        except Exception as e:
            print(f"[❌] Upload failed: {e}")
        finally:
            browser.close()

    tshark_proc.wait()
    print(f"✅ Upload capture done: {pcap_file}")

def sniff_all_cloud():
    links = load_links_from_excel("Cloud")[:2]
    for url, play_class, pre_class in links:
        sniff_cloud_upload(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_cloud()
