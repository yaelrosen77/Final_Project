import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel

wait_time = 30

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def try_iframes_for_game(driver,play_class) -> bool:
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    clicked = False
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            time.sleep(1)
            clicked = click_by_class(driver, play_class)
            driver.switch_to.default_content()
        except:
            driver.switch_to.default_content()
    return clicked

def sniff_game(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/game"            # this maps to your Windows ...\Crawler\game when using -v
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_game.pcap"
    print(f"\n🟢 Starting game capture for {app_name}...")

    options = uc.ChromeOptions()
    options.add_argument("--headless=new")          # <<< run headless in Docker
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"   # <<< tell it where Chromium is

    # Important: also pass the binary path to uc (helps with version mismatches)
    driver = uc.Chrome(options=options, browser_executable_path="/usr/bin/chromium")

    try:
        print(f"[⚙️] Opening: {url}")
        driver.get(url)
        time.sleep(5)

        clicked = False
        if play_class:
            clicked = click_by_class(driver, play_class)
        if not clicked and not try_iframes_for_game(driver, play_class):
            print("[❌] No play button found.")
            return

        print("[🎮] Starting tshark before game plays...")
        tshark_proc = subprocess.Popen(
            ["tshark", "-i", "eth0", "-a", f"duration:{wait_time}", "-w", pcap_file],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )

        print(f"[🎬] Playing game for {wait_time} seconds...")
        time.sleep(wait_time)

    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        driver.quit()
        if 'tshark_proc' in locals():
            tshark_proc.wait()
        print(f"✅ Game capture done: {pcap_file}")

def click_by_class(driver, class_name: str) -> bool:
    for by in [By.CLASS_NAME,By.ID]:
        try:
            elements = driver.find_elements(by, class_name)
            for element in elements:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(0.5)
                    element.click()
                    print(f"[+] Clicked element with class '{class_name}'")
                    return True
                except Exception:
                    continue
        except Exception:
            continue
    return False

def click_by_text(driver, text: str) -> bool:
    elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{text}')]")
    for element in elements:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            element.click()
            print(f"[+] Clicked element with text '{text}'")
            return True
        except Exception:
            continue
    return False

def sniff_all_games():
    links = load_links_from_excel("Games")[:3]
    for url, play_class, pre_class in links:
        sniff_game(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_games()
