import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from base_sniffer import BaseSniffer, load_links_from_excel

wait_time = 5

class DownloadSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class,"Download")

    def sniff(self):
        self.ensure_dir()
        self.setup_driver()
        try:
            self.setup_website()
            tshark_proc = subprocess.Popen(
                ["tshark", "-i", "eth0", "-a", "duration:40", "-w", self.pcap_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)
            existing_files = set(os.listdir(self.out_dir))   # Get list of files BEFORE clicking
            clicked = self.click_play_button()
            if self.play_class: self.try_iframes_in_iframe()
            if self.play_class: self.try_iframes()
            # if not clicked:
            #     try_click('a[href$=".pdf"], a[download], button:has-text("Download")', "Default")
            # if not clicked:
            #     try_click('[class*="download" i], [id*="download" i]', "Fallback")
            print("⏳ Waiting for file to be written...")
            time.sleep(wait_time)
            new_files = set(os.listdir(self.out_dir)) - existing_files
            if new_files:
                for file in new_files: print(f"[✅] File detected in folder: {file}")
            else: print("[❌] No file was downloaded or detected in folder.")
            time.sleep(5)
            tshark_proc.wait()
        except Exception as e:
            print(f"[⚠️] General error: {e}")
        finally:
            self.driver.quit()
            print(f"[✅] capture done: {self.pcap_file}")

def sniff_all_downloads():
    links = load_links_from_excel("Download")[16:]
    for url, play_class, skip_class in links:
        sniffer = DownloadSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_downloads()
