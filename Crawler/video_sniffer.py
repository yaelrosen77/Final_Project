import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel
from base_sniffer import BaseSniffer
wait_time = 5

class VideoSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class,"video")

    def click_outof_iframe(self,iframe):
        if not self.play_class: return False
        self.driver.switch_to.default_content()
        clicked = self.click_play_button()
        time.sleep(2)
        self.play_video_if_found()
        self.driver.switch_to.frame(iframe)
        return clicked
    def try_iframes_for_video(self):
        print(f"[🎬] Trying iframe...")
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                self.driver.switch_to.frame(iframe)
                time.sleep(2)
                clicked = True
                if self.play_class:
                    clicked = self.click_play_button()
                    if clicked and not self.click_outof_iframe(iframe):
                        self.try_iframes_for_video()
                    time.sleep(2)
                if clicked and self.play_video_if_found():
                    self.driver.switch_to.default_content()
                    return True
                self.driver.switch_to.default_content()
            except:
                self.driver.switch_to.default_content()
        return False

    def play_video_if_found(self):
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
        print(f"\n🟢 Starting video capture for {self.app_name}...")
        self.setup_driver()
        try:
            print(f"[⚙️] Opening: {self.url}")
            self.driver.get(self.url)
            try:
                time.sleep(2)
                self.driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")
                time.sleep(2)
            except Exception as e:
                print(f"[⚠️] Scroll error: {e}")
            clicked = True
            if self.play_class:
                clicked = self.click_play_button()
            time.sleep(5)
            played = self.play_video_if_found()
            if not clicked or not played:
                time.sleep(2)
                self.try_iframes_for_video()
        except Exception as e:
            print(f"[⚠️] General error: {e}")
        finally:
            self.driver.quit()
            print(f"[✅] Video capture done: {self.pcap_file}")

def sniff_all_videos():
    links = load_links_from_excel("Video Str.")[47:]
    for url, play_class, skip_class in links:
        sniffer = VideoSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_videos()
