import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel
from base_sniffer import BaseSniffer
wait_time = 1

class VideoSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class,"video")

    def play_if_found(self):
        try:
            self.driver.find_element(By.TAG_NAME, "video")
            time.sleep(2)
            self.driver.execute_script("""
                const video = document.querySelector('video');
                if (video) {
                    video.muted = true;
                    video.play().catch(() => {});
                }
            """)
            print(f"[🎬] Playing <video> for {wait_time} seconds...")
            tshark_proc = subprocess.Popen(
                ["tshark", "-i", "eth0", "-a", f"duration:{wait_time}", "-w", self.pcap_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(wait_time)
            tshark_proc.wait()
            return True
        except NoSuchElementException:
            print(f"[❌] Failed to play <video>")
            return False

    def sniff(self):
        self.ensure_dir()
        print(f"\n🟢 Starting capture for {self.app_name}...")
        self.setup_driver()
        try:
            self.setup_website()
            self.FooterAcceptCookie(self.skip_class)
            clicked = self.click_play_button()
            time.sleep(5)
            played = self.play_if_found()
            if not clicked or not played:
                time.sleep(2)
                self.try_iframes()
        except Exception as e:
            print(f"[⚠️] General error: {e}")
        finally:
            self.driver.quit()
            print(f"[✅] capture done: {self.pcap_file}")

def sniff_all_videos():
    links = load_links_from_excel("Video Str.")[24:] # [67:]
    for url, play_class, skip_class in links:
        sniffer = VideoSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_videos()
