import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel
from base_sniffer import BaseSniffer
from selenium.webdriver.remote.webelement import WebElement

wait_time = 1

import time
import pyautogui
from selenium.webdriver.common.by import By

class AudioSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class,"audio")

    def play_if_found(self):
        try:
            time.sleep(5)
            print(f"[🎬] Playing <audio> for {wait_time} seconds...")
            tshark_proc = subprocess.Popen(
                ["tshark", "-i", "eth0", "-a", f"duration:{wait_time}", "-w", self.pcap_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(wait_time)
            tshark_proc.wait()
            return True
        except NoSuchElementException:
            print(f"[❌] Failed to play <audio>")
            return False

    def sniff(self):
        self.ensure_dir()
        self.setup_driver()
        try:
            self.setup_website()
            self.click_shadow_button()
            clicked = self.click_play_button()
            time.sleep(5)
            if isinstance(clicked,WebElement):
                print("running <audio> play")
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clicked)
                clicked.click()
                self.driver.execute_script("arguments[0].muted = false; return arguments[0].play();", clicked)
                self.play_if_found()
            elif not self.play_class: self.play_if_found()
            else: self.try_iframes()
        except Exception as e:
            print(f"[⚠️] General error: {e}")
        finally:
            self.driver.quit()
            print(f"[✅] capture done: {self.pcap_file}")

def sniff_all_audios():
    links = load_links_from_excel("Audio Str.")[69:]  #[70:]
    for url, play_class, skip_class in links:
        sniffer = AudioSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_audios()
