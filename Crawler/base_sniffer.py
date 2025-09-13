import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel

wait_time = 2

def _get_chrome_major_version_windows():
    """Return installed Chrome major version (e.g., 139) on Windows."""
    if os.name != "nt":
        return None
    try:
        import winreg
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            try:
                k = winreg.OpenKey(root, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(k, "version")
                return int(version.split(".")[0])
            except OSError:
                pass
    except Exception:
        pass
    return None

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
        options.add_argument("--headless=new")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.binary_location = "/usr/bin/chromium"  # make sure Selenium knows where Chromium is

        # 🛠 pin UC to your installed Chrome major (e.g., 139)
        major = _get_chrome_major_version_windows()
        kwargs = {}
        if major:
            kwargs["version_main"] = major

        self.driver = uc.Chrome(options=options, **kwargs)
