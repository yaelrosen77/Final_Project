import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import tldextract
import pandas as pd

wait_time = 2

def load_links_from_excel(sheet_name: str, excel_path="App_direct_links.xlsx"):
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file '{excel_path}' not found")

    df = pd.read_excel(excel_path, sheet_name=sheet_name, header=None)
    urls = df[2].dropna().tolist()
    play_class_names = df[1].fillna("").tolist()
    pre_class_names = df[0].fillna("").tolist()

    results = []
    for i in range(len(urls)):
        url = urls[i]
        extra = play_class_names[i] if i < len(play_class_names) else ""
        pre_extra = pre_class_names[i] if i < len(pre_class_names) else ""
        if isinstance(url, str) and url.startswith("http"):
            results.append((url, extra, pre_extra))
    return results
def get_app_name(url):
    extracted = tldextract.extract(url)
    app_name = extracted.domain
    if app_name:
        app_name = app_name.replace('-', ' ').capitalize().replace(' ', '')
    return app_name

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
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.driver = uc.Chrome(options=options)
        try: version = self.driver.capabilities.get("browserVersion")
        except: pass
    def setup_website(self):
        print(f"\n🟢 Starting capture for {self.app_name} with: {self.url}")
        self.driver.get(self.url)
        try:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys("thisisunsafe").perform()
            print("⚠️ Bypassed SSL warning screen with 'thisisunsafe'")
        except Exception as e:
            print(f"❌ SSL bypass failed or not needed: {e}")
        try:
            time.sleep(2)
            self.driver.execute_script("(document.scrollingElement || document.documentElement).scrollTo({top: 99999, behavior: 'smooth'});")
            time.sleep(2)
            self.driver.execute_script("(document.scrollingElement || document.documentElement).scrollTo({ top: 0, behavior: 'smooth' });")
            time.sleep(2)
        except Exception as e:
            print(f"[⚠️] Scroll error: {e}")
    def start_pcap_sniffing(self):
        tshark_proc = subprocess.Popen(
            ["tshark", "-i", "eth0", "-a", "duration:40", "-w", self.pcap_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return tshark_proc

    def click_shadow_button(self):
        if not self.skip_class or isinstance(self.skip_class,int): return
        print("############### shadow_button ##############  ", end='')
        try:
            shadow_hosts = self.driver.execute_script("""
                return Array.from(document.querySelectorAll("*"))
                    .filter(el => el.shadowRoot !== null);
            """)
            if not shadow_hosts: print(f"❌ - No shadow_hosts")
            for host in shadow_hosts:
                clicked = self.driver.execute_script("""
                    const footer = arguments[0];
                    const selector = arguments[1];
                    const root = footer.shadowRoot;
                    if (!root) return false;
                    const btn = root.querySelector(selector);
                    if (btn) {
                        btn.focus();
                        btn.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                        btn.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                        btn.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        return true;
                    }
                    return false;
                """, host, self.skip_class)
                if clicked:
                    self.skip_class = ""
                    print(f"✅ - Clicked '{self.skip_class}'")
                    return
                else:
                    print(f"❌ - Couldn't find '{self.skip_class}'")
        except Exception as e: print("❌ - No shadow DOM found")

    def play_if_found(self): pass

    def click_play_button(self, tries=0):
        if not self.play_class: return True
        print("############# click_play_button ############  ", end='')
        time.sleep(2)
        groups = [name.strip() for name in self.play_class.split(",") if name.strip()]
        selectors = [By.ID, By.CLASS_NAME]
        nameDone = [False for _ in range(len(groups))]
        notFoundSoUnloaded = True
        tries += 1
        for i,name in enumerate(groups):
            for by in selectors:
                try:
                    elements = self.driver.find_elements(by,name) if name[0]!=':' else self.driver.find_elements(By.XPATH,f"//button[contains(normalize-space(string()),'{name[1:]}')]")
                    if len(elements) > 0: notFoundSoUnloaded = False
                    for element in elements:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            if element.tag_name.lower() == "audio": return element
                            element.click()
                            print(f"✅ - Clicked '{name}'")
                            self.after_click(name)
                            nameDone[i] = True
                            time.sleep(3)
                            break
                        except: continue
                except Exception as e:
                    print(f"❌ - Couln't find {name}")
                    continue
                if nameDone[i]: break
        if notFoundSoUnloaded:
            if tries > 2:
                print(f"❌ - Unloaded '{self.play_class}'")
                return False
            self.click_play_button(tries)
        for curNameDone in nameDone:
            if curNameDone: return True
        return False
    def after_click(self, name):
        self.play_class = ",".join([c for c in self.play_class.split(",") if c.strip() != name])

    def try_iframes(self):
        print(f"################## iframe ##################  ", end='')
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            if self.handle_iframe(iframe): return True
        return False
    def click_outof_iframe(self):
        if not self.play_class: return True
        self.driver.switch_to.default_content()
        clicked = self.click_play_button()
        time.sleep(2)
        self.play_if_found()
        return clicked

    def try_iframes_in_iframe(self):
        try:
            print(f"############# iframe in iframe #############  ", end='')
            self.driver.switch_to.default_content()
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                self.driver.switch_to.frame(iframe)
                iframes2 = self.driver.find_elements(By.TAG_NAME, "iframe")
                for iframe2 in iframes2:
                    if self.handle_iframe(iframe2): return True
            return False
        except Exception as e: return False

    def handle_iframe(self, iframe):
        try:
            self.driver.switch_to.frame(iframe)
            time.sleep(2)
            clicked = self.click_play_button()
            if clicked and not self.click_outof_iframe():
                self.try_iframes()
            time.sleep(2)
            if clicked and self.play_if_found():
                self.driver.switch_to.default_content()
                return True
            self.driver.switch_to.default_content()
        except:
            self.driver.switch_to.default_content()
        return False
