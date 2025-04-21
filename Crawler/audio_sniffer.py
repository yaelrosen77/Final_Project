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

def sniff_audio(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/audio"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_audio.pcap"
    print(f"\n🟢 Starting audio capture for {app_name}...")

    time.sleep(1)
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    driver = uc.Chrome(options=options)

    try:
        print(f"[⚙️] Opening: {url}")
        driver.get(url)
        time.sleep(2)

        tshark_proc = subprocess.Popen(
            ["tshark", "-i", "eth0", "-a", f"duration:{wait_time}", "-w", pcap_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if play_class:
            try:
                clicked = click_play_button(driver, play_class)
                if not clicked:
                    try_iframes_for_audio(driver,pcap_file)
            except Exception as e:
                print(f"[!] Error during click: {e}")

        time.sleep(wait_time)
        tshark_proc.wait()

    except Exception as e:
        print(f"[!] General error: {e}")
    finally:
        driver.quit()
        print(f"✅ audio capture done: {pcap_file}")

def click_play_button(driver, class_names: str) -> bool:
    class_groups = [cls.strip() for cls in class_names.split(",") if cls.strip()]
    for class_name in class_groups:
        elements = driver.find_elements(By.CSS_SELECTOR, f".{class_name}")
        for element in elements:
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.5)
                element.click()
                print(f"[+] Clicked element with class '{class_name}'")
                return True
            except Exception:
                continue
    return False

def try_iframes_for_audio(driver, pcap_file) -> bool:
    return False

def sniff_all_audios():
    links = load_links_from_excel("Audio Str.")[:2] #[21:]
    for url, play_class, pre_class in links:
        sniff_audio(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_audios()
