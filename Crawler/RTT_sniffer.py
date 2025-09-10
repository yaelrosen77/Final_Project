import time
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from base_sniffer import BaseSniffer, load_links_from_excel

CAPTURE_LIMIT_SEC = 30     # כמה שניות לצלם לכל אתר
PAGE_LOAD_WAIT = 6         # לתת לדף לעלות ולפתוח סוקט/פולינג
INTERACTION_SEC = 12       # אינטראקציה קלה כדי לשמור את הדף "חי"

GENERIC_TICKER_SELECTORS = [
    # מנסים לגלול/לפקסס ליד אזורי טיקר נפוצים כדי לייצר עדכונים
    '[class*="ticker"]',
    '[class*="marquee"]',
    '[class*="scroll"]',
    '[class*="live"]',
    '[class*="prices"]',
    '[class*="market"]',
    '[data-test*="ticker"]',
    'section[role="feed"]',
]

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

        # פוקוס על אזור שנראה כמו טיקר/מחירים כדי לעורר Mutation/WebSocket/polling
        try:
            for sel in GENERIC_TICKER_SELECTORS:
                el = self.driver.execute_script("return document.querySelector(arguments[0]);", sel)
                if el:
                    self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", el)
                    try:
                        ActionChains(self.driver).move_to_element(el).pause(0.2).perform()
                    except Exception:
                        pass
                    break
        except Exception:
            pass

    def sniff(self):
        self.ensure_dir()
        self.setup_driver()
        try:
            self.setup_website()
            time.sleep(PAGE_LOAD_WAIT)

            # התחלת הקלטה (pcap) – ה-Base מגדיר את tshark/דגלים
            cap = self.start_pcap_sniffing()

            # אינטראקציה קלה שתגרום לדף לפתוח/להמשיך ערוצי עדכון חיים
            t0 = time.time()
            while time.time() - t0 < INTERACTION_SEC:
                self._nudge_page()
                time.sleep(0.8)

            # השלם עד סוף חלון הצילום הכולל כדי ללכוד עוד עדכונים חיים
            left = CAPTURE_LIMIT_SEC - (time.time() - t0) - PAGE_LOAD_WAIT
            if left > 0:
                time.sleep(left)

            try:
                cap.wait(timeout=3)
            except Exception:
                pass
        finally:
            try:
                self.driver.quit()
            except Exception:
                pass


def sniff_all_tickers():
    """
    אם יש לך אקסל עם רשימת אתרים – טען משם.
    אחרת, פשוט בנה כאן רשימה ידנית (urls) והריץ.
    """
    try:
        # דוגמה: גיליון בשם "Tickers" עם עמודה URL (כמו בשאר הסניפרים שלך)
        links = load_links_from_excel("Tickers")
        urls = [u for (u, *_rest) in links]
    except Exception:
        # fallback – הדבק כאן רשימת URL ידנית אם צריך
        urls = [
            "https://www.bloomberg.com/markets",
            "https://finance.yahoo.com/",
            "https://www.tradingview.com/",
            "https://www.reuters.com/markets",
            "https://www.coinmarketcap.com/",
        ]

    for url in urls:
        sniffer = TickerSniffer(url)
        sniffer.sniff()


if __name__ == "__main__":
    sniff_all_tickers()
