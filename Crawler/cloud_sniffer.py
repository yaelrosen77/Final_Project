import time
import os
import subprocess
from playwright.sync_api import sync_playwright
from base_sniffer import BaseSniffer, get_app_name, load_links_from_excel

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
def sniff_cloud_upload(url, play_class="", pre_class=""):
    app_name = get_app_name(url)
    out_dir = f"/app/cloud"
    ensure_dir(out_dir)
    pcap_file = f"{out_dir}/{app_name}_upload.pcap"
    html_file = f"{out_dir}/{app_name}_html.html"

    print(f"\n🟢 Starting cloud upload capture for {app_name}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        try:
            page.goto(url, timeout=90000, wait_until="domcontentloaded")

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"[📄] HTML saved to {html_file}")

            fake_file = os.path.abspath("dummy_upload.txt")
            with open(fake_file, "w") as f:
                f.write("This is a dummy file.")

            input_selector = 'input[type="file"]'
            page.wait_for_selector(input_selector, timeout=10000, state="attached")

            tshark_proc = subprocess.Popen(
                ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(1)

            page.set_input_files(input_selector, fake_file)
            print(f"[📤] File uploaded using {input_selector}")

            try:
                submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
                if submit_btn:
                    submit_btn.click()
                    print("[🖱️] Clicked submit button.")
            except:
                print("[ℹ️] No clickable submit button found.")

            # ← כאן התנאי המתוקן: רק אם play_class לא ריק
            if isinstance(play_class, str) and play_class.strip() != '':
                try:
                    class_btn = page.query_selector(f'.{play_class}')
                    if class_btn:
                        class_btn.click()
                        print(f"[🖱️] Clicked button with class: {play_class}")
                    else:
                        print(f"[ℹ️] No button found with class: {play_class}")
                except Exception as e:
                    print(f"[⚠️] Failed to click class button: {e}")

            time.sleep(4)
            os.remove(fake_file)

        except Exception as e:
            print(f"[❌] Upload failed: {e}")
        finally:
            browser.close()

    tshark_proc.wait()
    print(f"✅ Upload capture done: {pcap_file}")

def sniff_all_cloud():
    links = load_links_from_excel("Cloud")[29:]
    for url, play_class, pre_class in links:
        sniff_cloud_upload(url, play_class, pre_class)

if __name__ == "__main__":
    sniff_all_cloud()
#
# import time
# import os
# import subprocess
# from playwright.sync_api import sync_playwright
# from utils import get_app_name
# from excel_loader import load_links_from_excel
#
# def ensure_dir(path):
#     if not os.path.exists(path):
#         os.makedirs(path)
#
# def sniff_cloud_upload(requires_login, url, play_class="", pre_class=""):
#     app_name = get_app_name(url)
#     out_dir = f"/app/cloud"
#     ensure_dir(out_dir)
#     pcap_file = f"{out_dir}/{app_name}_upload.pcap"
#     html_file = f"{out_dir}/{app_name}_html.html"
#
#     print(f"\n🟢 Starting cloud upload capture for {app_name}...")
#
#     if requires_login == "yes":
#         print("[🔐] Login required for this URL.")
#     else:
#         print("[🔓] No login required for this URL.")
#
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         context = browser.new_context()
#         page = context.new_page()
#
#         try:
#             page.goto(url, timeout=110000, wait_until="domcontentloaded")
#
#             with open(html_file, "w", encoding="utf-8") as f:
#                 f.write(page.content())
#             print(f"[📄] HTML saved to {html_file}")
#
#             fake_file = os.path.abspath("dummy_upload.txt")
#             with open(fake_file, "w") as f:
#                 f.write("This is a dummy file.")
#
#             input_selector = 'input[type="file"]'
#             page.wait_for_selector(input_selector, timeout=10000, state="attached")
#
#             tshark_proc = subprocess.Popen(
#                 ["tshark", "-i", "eth0", "-a", "duration:40", "-w", pcap_file],
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL,
#             )
#             time.sleep(1)
#
#             page.set_input_files(input_selector, fake_file)
#             print(f"[📤] File uploaded using {input_selector}")
#
#             try:
#                 submit_btn = page.query_selector('button[type="submit"], input[type="submit"]')
#                 if submit_btn:
#                     submit_btn.click()
#                     print("[🖱️] Clicked submit button.")
#
#                     if requires_login == "yes":
#                         print("[🔐] Login required — checking for login page after upload...")
#
#                         login_detected = False
#                         try:
#                             # Look for login fields (after button click)
#                             page.wait_for_selector('input[type="email"], input[name="username"], input[name="login"]',
#                                                    timeout=5000)
#                             login_detected = True
#                         except:
#                             print("[ℹ️] No login form detected after upload attempt.")
#
#                         if login_detected:
#                             print("[🔑] Login form detected. Attempting to log in...")
#                             try:
#                                 # Fill in email or username
#                                 if page.query_selector('input[type="email"]'):
#                                     page.fill('input[type="email"]', "fewshotproject@yahoo.com")
#                                 elif page.query_selector('input[name="username"]'):
#                                     page.fill('input[name="username"]', "fewshotproject@yahoo.com")
#
#                                 # Fill in password
#                                 page.fill('input[type="password"]', "Xt!.CJZBdmK!5t4")
#
#                                 # Submit the login form
#                                 login_submit = page.query_selector('button[type="submit"], input[type="submit"]')
#                                 if login_submit:
#                                     login_submit.click()
#                                     print("[✅] Submitted login form.")
#
#                                 # Wait for redirect to complete
#                                 page.wait_for_load_state("networkidle", timeout=10000)
#                                 print(f"[🌐] Redirected to: {page.url}")
#
#                             except Exception as e:
#                                 print(f"[❌] Login attempt failed: {e}")
#             except:
#                 print("[ℹ️] No clickable submit button found.")
#
#             # ← כאן התנאי המתוקן: רק אם play_class לא ריק
#             if isinstance(play_class, str) and play_class.strip() != '':
#                 try:
#                     class_btn = page.query_selector(f'.{play_class}')
#                     if class_btn:
#                         class_btn.click()
#                         print(f"[🖱️] Clicked button with class: {play_class}")
#                     else:
#                         print(f"[ℹ️] No button found with class: {play_class}")
#                 except Exception as e:
#                     print(f"[⚠️] Failed to click class button: {e}")
#
#             time.sleep(4)
#             os.remove(fake_file)
#
#         except Exception as e:
#             print(f"[❌] Upload failed: {e}")
#         finally:
#             browser.close()
#
#     tshark_proc.wait()
#     print(f"✅ Upload capture done: {pcap_file}")
#
# def sniff_all_cloud():
#     links = load_links_from_excel("Cloud")
#     threshold = 3
#     for i, (url, play_class, pre_class) in enumerate(links):
#         requires_login = "yes" if i >= threshold else "no"
#         sniff_cloud_upload(requires_login, url, play_class, pre_class)
#
# if __name__ == "__main__":
#     sniff_all_cloud()
