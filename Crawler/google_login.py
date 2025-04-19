import undetected_chromedriver as uc
import time
import os

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# תיקיית פרופיל קבוע בדוקר
PROFILE_PATH = "/app/chrome-profile"
ensure_dir(PROFILE_PATH)

def open_google_login():
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={PROFILE_PATH}")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    # אל תוסיף headless – כי רוצים לראות

    driver = uc.Chrome(options=options)

    print("🔐 Opening Google login page...")
    driver.get("https://accounts.google.com/")

    print("👉 Please log in manually in the browser window that opened.")
    print("✅ Once you’re logged in, close the browser to finish.")

    # מחכה עד שהמשתמש יסגור ידנית
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("👋 Exiting login script.")
        driver.quit()

if __name__ == "__main__":
    open_google_login()
