import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from base_sniffer import BaseSniffer
from excel_loader import load_links_from_excel
from selenium.webdriver.common.keys import Keys

wait_time = 5


class GameSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class, "audio")
        self.nicknamed_filled = False

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
            self.fill_nickname_field()
            self.enter_focused()
            clicked = self.click_play_button()
            time.sleep(5)
            if not self.play_class: self.play_if_found()
            else: self.try_iframes()
            if self.play_class: self.try_iframes_in_iframe()
        except Exception as e:
            print(f"[⚠️] General error: {e}")
        finally:
            self.driver.quit()
            print(f"[✅] capture done: {self.pcap_file}")

    def after_click(self, name):
        super().after_click(name)
        self.click_shadow_button_everywhere()
        self.fill_nickname_field()

    def enter_focused(self):
        if not self.play_class:
            print("################# enter_focused ################  ", end='')
            try:
                focused = self.driver.switch_to.active_element
                focused.send_keys(Keys.ENTER)
                print("✅")
            except Exception as e:
                print("❌:", e)
    def fill_nickname_field(self, value="sinale"):
        if self.nicknamed_filled: return
        print("############ fill_nickname_field ###########  ", end='')
        inputs = self.driver.find_elements(By.TAG_NAME, "input")
        keywords = ["name", "nickname", "displayname"]
        for input_el in inputs:
            try:
                attrs = {
                    "name": input_el.get_attribute("name") or "",
                    "id": input_el.get_attribute("id") or "",
                    "placeholder": input_el.get_attribute("placeholder") or ""
                }
                for attr_value in attrs.values():
                    if any(k in attr_value.lower() for k in keywords):
                        input_el.clear()
                        input_el.send_keys(value)
                        print(f"✅")
                        self.nicknamed_filled = True
                        return
            except Exception as e: continue
        print("❌")
        return False
    def click_shadow_button_everywhere(self, max_depth=5, depth=0):
        if not self.skip_class: return
        print("############# shadow_button_everywhere #############  ", end='')
        try:
            if depth == 0: self.driver.switch_to.default_content()
            self.click_shadow_button()
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    self.click_shadow_button()
                    if depth < max_depth:
                        self.click_shadow_button_everywhere(max_depth, depth + 1)
                    self.driver.switch_to.default_content()
                except:
                    self.driver.switch_to.default_content()
                    continue
        except Exception as e: print("❌")

def sniff_all_games():
    links = load_links_from_excel("Games")[11:]  # [11:]
    for url, play_class, skip_class in links:
        sniffer = GameSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_games()
