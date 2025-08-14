import time
import subprocess
from playwright.sync_api import sync_playwright
from base_sniffer import BaseSniffer, load_links_from_excel

class BrowserSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class,"Browser")

    def sniff(self):
        self.ensure_dir()
        html_file = f"{self.out_dir}/{self.app_name}_html.html"
        print(f"\n🟢 Starting capture for {self.app_name} with: {self.url}")
        tshark_proc = subprocess.Popen(
            ["tshark", "-i", "eth0", "-a", "duration:40", "-w", self.pcap_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Set to "False" to see what happens
            context = browser.new_context()
            page = context.new_page()
            try:
                page.goto(self.url, timeout=60000, wait_until="domcontentloaded")
                with open(html_file, "w", encoding="utf-8") as f:                                     # Save the HTML content
                    f.write(page.content())
                print(f"[📄] HTML saved to {html_file}")
                for _ in range(3):                                                                    # Scroll and interact with the page
                    page.mouse.wheel(0, 1000)
                    time.sleep(1)
                    page.mouse.wheel(0, -500)
                    time.sleep(1)
                links = page.query_selector_all(f"a[href^='/'], a[href*='{self.app_name.lower()}']")  # Try clicking 2 internal or site-related links
                for i in range(min(2, len(links))):
                    try:
                        print(f"[🖱️] Clicking link {i+1}")
                        links[i].click(timeout=5000)
                        time.sleep(5)
                    except: continue
            except Exception as e: print(f"[⚠️] General error: {e}")
            finally:
                browser.close()
                print(f"[✅] capture done: {self.pcap_file}")
        tshark_proc.wait()

def sniff_all_browsing():
    links = load_links_from_excel("Browsing")
    for url, play_class, skip_class in links:
        sniffer = BrowserSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_browsing()
