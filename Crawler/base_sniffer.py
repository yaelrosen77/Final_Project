import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel

wait_time = 2

class BaseSniffer:
    def __init__(self, url, play_class="", skip_class="", out_dir=""):
        self.out_dir = f"/app/{out_dir}"
        self.url = url
        self.play_class = play_class
        self.skip_class = skip_class
        self.app_name = get_app_name(url)
        self.pcap_file = f"{self.out_dir}/{self.app_name}_video.pcap"
        self.driver = None

    def ensure_dir(self):
        if not os.path.exists(self.out_dir):
            os.makedirs(self.out_dir)

    def setup_driver(self):
        options = uc.ChromeOptions()
        # options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = uc.Chrome(options=options)

    def click_play_button(self, tries=0):
        time.sleep(2)
        groups = [name.strip() for name in self.play_class.split(",") if name.strip()]
        selectors = [By.ID, By.CLASS_NAME]
        nameDone = [False for _ in range(len(groups))]
        notFoundSoUnloaded = True
        tries += 1
        for i,name in enumerate(groups):
            for by in selectors:
                try:
                    elements = self.driver.find_elements(by, name)
                    if len(elements) > 0: notFoundSoUnloaded = False
                    for element in elements:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            element.click()
                            print(f"[+] Clicked element with '{name}'")
                            self.play_class = ",".join([c for c in self.play_class.split(",") if c.strip() != name])
                            nameDone[i] = True
                            break
                        except: continue
                except Exception as e:
                    print(f"[!] Failed to click element with {name}")
                    continue
                if nameDone[i]: break
        if notFoundSoUnloaded:
            print(f"[⚠️] Unloaded '{self.play_class}'")
            if tries > 2:
                print(f"[⚠️] Failed to load '{self.play_class}'")
                return False
            self.click_play_button(tries)
        for curNameDone in nameDone:
            if curNameDone: return True
        return False
