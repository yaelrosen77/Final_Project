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
    def setup_website(self):
        print(f"[⚙️] Opening: {self.url}")
        self.driver.get(self.url)
        # try:
        #     from selenium.webdriver.common.action_chains import ActionChains
        #     ActionChains(self.driver).send_keys("thisisunsafe").perform()
        #     print("⚠️ Bypassed SSL warning screen with 'thisisunsafe'")
        # except Exception as e:
        #     print(f"❌ SSL bypass failed or not needed: {e}")
        try:
            time.sleep(2)
            self.driver.execute_script("window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo({ top: 0, behavior: 'smooth' });")
            time.sleep(2)
        except Exception as e:
            print(f"[⚠️] Scroll error: {e}")

    def FooterAcceptCookie(self, shadowRootElem):
        try:
            shadow_hosts = self.driver.execute_script("""
                return Array.from(document.querySelectorAll("*"))
                    .filter(el => el.shadowRoot !== null);
            """)
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
                """, host, shadowRootElem)
                if clicked:
                    print(f"✅ Clicked '{shadowRootElem}' inside <page-footer>'s shadow DOM")
                    return
                else:
                    print(f"❌ Could not find '{shadowRootElem}' button inside shadow DOM")
        except Exception as e:
            print("No page-footer's shadow DOM found")

    def play_if_found(self): pass

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
                    elements = self.driver.find_elements(by,name) if name[0]!=':' else self.driver.find_elements(By.XPATH,f"//button[contains(normalize-space(string()),'{name[1:]}')]")
                    if len(elements) > 0: notFoundSoUnloaded = False
                    for element in elements:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            if element.tag_name.lower() == "audio": return element
                            element.click()
                            print(f"[+] Clicked element with '{name}'")
                            self.play_class = ",".join([c for c in self.play_class.split(",") if c.strip() != name])
                            nameDone[i] = True
                            time.sleep(1)
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

    def try_iframes(self):
        print(f"[🎬] Trying iframe...")
        self.driver.switch_to.default_content()
        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
        for iframe in iframes:
            try:
                self.driver.switch_to.frame(iframe)
                time.sleep(2)
                clicked = True
                if self.play_class:
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
    def click_outof_iframe(self):
        if not self.play_class: return False
        self.driver.switch_to.default_content()
        clicked = self.click_play_button()
        time.sleep(2)
        self.play_if_found()
        return clicked
