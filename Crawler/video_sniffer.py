import time
import os
import subprocess
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from utils import get_app_name
from excel_loader import load_links_from_excel

wait_time = 15

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def sniff_video(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/video"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_video.pcap"
    print(f"\n🟢 Starting video capture for {app_name}...")

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

        if play_class:
            try:
                clicked = click_play_button(driver, play_class)
                if not clicked:
                    try_iframes_for_video(driver,pcap_file)
            except Exception as e:
                print(f"[⚠️] Error during click: {e}")
        time.sleep(1)
        videoFound = play_video_if_found(driver,pcap_file)
        if not videoFound:
            try_iframes_for_video(driver,pcap_file)
    except Exception as e:
        print(f"[⚠️] General error: {e}")
    finally:
        driver.quit()
        print(f"[✅] Video capture done: {pcap_file}")

def click_play_button(driver, class_or_id_names: str) -> bool:
    groups = [name.strip() for name in class_or_id_names.split(",") if name.strip()]
    selectors = [By.ID,By.CLASS_NAME]
    for name in groups:
        curNameDone = False
        for by in selectors:
            try:
                elements = driver.find_elements(by, name)
                for element in elements:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.5)
                        element.click()
                        print(f"[+] Clicked element with class '{name}'")
                        curNameDone = True
                        break
                    except Exception: continue
            except Exception as e:
                print(f"[!] Failed to click element with {name}")
                continue
            if curNameDone: break
    return curNameDone

def try_iframes_for_video(driver,pcap_file) -> bool:
    print(f"[🎬] Trying iframe")
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for iframe in iframes:
        try:
            driver.switch_to.frame(iframe)
            time.sleep(1)
            if play_video_if_found(driver,pcap_file):
                driver.switch_to.default_content()
                return True
            driver.switch_to.default_content()
        except:
            driver.switch_to.default_content()
    return False

def play_video_if_found(driver, pcap_file) -> bool:
    try:
        video = driver.find_element(By.TAG_NAME, "video")
        driver.execute_script("""
            const video = document.querySelector('video');
            if (video) {
                video.muted = true;
                video.play().catch(() => {});
                if (video.requestFullscreen) {
                    video.requestFullscreen().catch(() => {});
                }
            }
        """)
        print(f"[🎬] Playing <video> for {wait_time} seconds...")
        tshark_proc = subprocess.Popen(
            ["tshark", "-i", "eth0", "-a", f"duration:{wait_time}", "-w", pcap_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            time.sleep(wait_time)
        finally:
            tshark_proc.wait()
        return True
    except NoSuchElementException:
        print(f"[❌] Failed to play <video>")
        return False

def sniff_all_videos():
    links = load_links_from_excel("Video Str.")[24:]
    for url, play_class, pre_class in links:
        sniff_video(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_videos()
