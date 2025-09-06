import os, time, tempfile, shutil
from urllib.parse import urlparse
from datetime import datetime

from selenium.webdriver.common.action_chains import ActionChains
from base_sniffer import BaseSniffer, load_links_from_excel

OUTPUT_DIR = "sniff_maps_pcap"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# אותם פרמטרים שהיו לך
CAPTURE_LIMIT_SEC = 25      # משך צילום לכל אתר (כולל אינטראקציה)
PAGE_LOAD_WAIT = 6          # המתנה אחרי טעינת הדף לפני תזוזה
INTERACTION_SEC = 12        # משך "טיול" במפה (pan/zoom)

class MapSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class, "Map")


    def sniff(self):
        self.ensure_dir()          # תיקיית פלט לפי הקטגוריה/אפליקציה
        self.setup_driver()        # יצירת ה-driver דרך ה-Base (כולל uc/פרופיל וכו' אם מוגדר שם)
        try:
            self.setup_website()   # לוגיקת הכנה כללית שלך (עקיפת SSL/גלילה קלה וכו' אם יש ב-Base)
            time.sleep(PAGE_LOAD_WAIT)
            tshark_proc = self.start_pcap_sniffing()

            clicked = self.click_play_button()
            if self.play_class: self.try_iframes_in_iframe()
            if self.play_class: self.try_iframes()

            self.goToLocation()

            w = self.driver.execute_script("return window.innerWidth;")
            h = self.driver.execute_script("return window.innerHeight;")
            cx, cy = int(w / 2), int(h / 2)
            self.driver.execute_script("""
                const el = document.elementFromPoint(arguments[0], arguments[1]);
                if (el) el.scrollIntoView({behavior: 'instant', block: 'center', inline: 'center'});
            """, cx, cy)
            ActionChains(self.driver).move_by_offset(0, 0).move_by_offset(cx, cy).click().perform()
            ActionChains(self.driver).move_by_offset(-cx, -cy).perform()  # קליק לפוקוס
            t0 = time.time()
            while time.time() - t0 < INTERACTION_SEC:
                ActionChains(self.driver).move_by_offset(cx, cy).click_and_hold().move_by_offset(180,
                                                                                                 10).release().perform()
                ActionChains(self.driver).move_by_offset(-cx - 180, -cy - 10).perform()  # PAN ימינה
                time.sleep(0.35)
                ActionChains(self.driver).move_by_offset(cx, cy).click_and_hold().move_by_offset(-160,
                                                                                                 -15).release().perform()
                ActionChains(self.driver).move_by_offset(-cx + 160, -cy + 15).perform()  # PAN שמאלה
                time.sleep(0.35)
                self.driver.execute_script("""  
                            const e1 = new WheelEvent('wheel', {deltaY: -220});
                            const e2 = new WheelEvent('wheel', {deltaY:  220});
                            const el = document.elementFromPoint(arguments[0], arguments[1]);
                            el.dispatchEvent(e1);
                            el.dispatchEvent(e2);
                        """, cx, cy)  # ZOOM IN/OUT
                time.sleep(0.3)
            tshark_proc.wait()
        finally:
            self.driver.quit()

    def after_click(self, name):
        super().after_click(name)
        self.click_shadow_button()

    def goToLocation(self):
        try:
            origin = self.driver.execute_script("return location.origin")
            self.driver.execute_cdp_cmd("Browser.grantPermissions", {
                "origin": origin,
                "permissions": ["geolocation"]
            })
            self.driver.execute_script("""
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(()=>{}, ()=>{});
                }
            """)
        except Exception as e:
            print(f"⚠️ Geolocation grant failed: {e}")

def sniff_all_maps():
    links = load_links_from_excel("Maps")[38:]
    for url, play_class, skip_class in links:
        sniffer = MapSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_maps()
