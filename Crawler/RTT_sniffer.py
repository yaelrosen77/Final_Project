import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from base_sniffer import BaseSniffer, load_links_from_excel

CAPTURE_LIMIT_SEC = 30     # כמה שניות לצלם לכל אתר
PAGE_LOAD_WAIT = 6         # לתת לדף לעלות ולפתוח סוקט/פולינג
INTERACTION_SEC = 12       # אינטראקציה קלה כדי לשמור את הדף "חי"

class TickerSniffer(BaseSniffer):
    def __init__(self, url, play_class="", skip_class=""):
        super().__init__(url, play_class, skip_class, "Ticker")

    def _nudge_page(self):
        """אינטראקציה כללית שמעודדת עדכונים חיים (ללא תלות באתר מסוים)."""
        try:
            # גלילה קלה מעלה/מטה
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(0.3)
            h = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight) || 2000;")
            self.driver.execute_script("window.scrollTo(0, Math.min(1200, arguments[0]-800));", h)
            time.sleep(0.3)
            self.driver.execute_script("window.scrollBy(0, -300);")
        except Exception:
            pass

    def sniff(self):
        self.ensure_dir()
        self.setup_driver()
        try:
            self.setup_website()
            time.sleep(PAGE_LOAD_WAIT)

            self.click_shadow_button()
            clicked = self.click_play_button()
            if self.play_class: self.try_iframes_in_iframe()
            if self.play_class: self.try_iframes()

            tshark_proc = self.start_pcap_sniffing()

            t0 = time.time()
            while time.time() - t0 < INTERACTION_SEC:
                self._nudge_page()
                time.sleep(0.8)
            left = CAPTURE_LIMIT_SEC - (time.time() - t0) - PAGE_LOAD_WAIT
            if left > 0:
                time.sleep(left)

            tshark_proc.wait()
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass

def sniff_all_tickers():
    links = load_links_from_excel("RTT")[78:]
    for url, play_class, skip_class in links:
        sniffer = TickerSniffer(url, play_class, skip_class)
        sniffer.sniff()

if __name__ == "__main__":
    sniff_all_tickers()
