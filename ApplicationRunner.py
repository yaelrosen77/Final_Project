import time
import tldextract
import os
from playwright.sync_api import sync_playwright

#receive a URL and extract the name of it's corresponding app
def get_app_name(url):
    extracted = tldextract.extract(url)
    app_name = extracted.domain
    if app_name:
        app_name = app_name.replace('-', ' ').capitalize().replace(' ', '')
    return app_name

#recieve URL and a session type and generates relevant network traffic
def simulate_network_session(url, session_type):
    if session_type == 'streaming':
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print(f"Opening: {url}")
            page.goto(url)

            try:
                page.click('text=Accept All', timeout=5000)
            except:
                pass

            try:
                page.wait_for_selector("video", timeout=10000)
                page.evaluate('''() => {
                            const video = document.querySelector('video');
                            if (video) {
                                video.muted = true;
                                video.play().catch(() => {});
                            }
                        }''')
                print(f"Streaming video for {30} seconds...")
            except:
                print("No <video> tag found. This page might not contain a standard HTML5 video.")

        time.sleep(30)
        browser.close()
        print("Done streaming.")

    elif session_type == 'file_upload':
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            print(f"Opening: {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            try:
                fake_file_path = os.path.abspath("dummy_upload.txt")
                with open(fake_file_path, "w") as f:
                    f.write("This is a dummy file for upload test.")

                # Find the input type=file element and set the file
                input_selector = 'input[type="file"]'
                page.wait_for_selector(input_selector, timeout=10000)
                page.set_input_files(input_selector, fake_file_path)
                print("File selected for upload.")

                try:
                    page.click('button[type="submit"], input[type="submit"]', timeout=5000)
                    print("Clicked submit/upload button.")
                except:
                    print("No explicit submit button found, file might auto-upload.")

                time.sleep(10)
                os.remove(fake_file_path)

            except Exception as e:
                print(f"File upload failed: {e}")

            browser.close()
            print("Session complete.")

    elif session_type == 'file_download':
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()

            print(f"Opening: {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            try:
                download_selector = 'a[href$=".pdf"], a[download], button:has-text("Download")'
                page.wait_for_selector(download_selector, timeout=10000)

                page.click(download_selector)
                print("Download triggered.")

                time.sleep(7)
            except Exception as e:
                print(f"Failed to trigger download: {e}")

            browser.close()
            print("Download session complete.")

    elif session_type == 'browsing':
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            print(f"Opening: {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            try:
                print("Simulating scroll behavior...")
                for i in range(0, 3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(1)
                    page.mouse.wheel(0, -500)
                    time.sleep(1)

                print("Looking for internal links to click...")
                links = page.query_selector_all("a[href^='/'], a[href*='" + tldextract.extract(url).domain + "']")
                if links:
                    for i in range(min(2, len(links))):
                        try:
                            links[i].click(timeout=5000)
                            print("Clicked an internal link.")
                            time.sleep(5)  # Wait after click
                        except:
                            continue
                else:
                    print("No internal links found.")

            except Exception as e:
                print(f"Browsing session failed: {e}")

            browser.close()
            print("Browsing session complete.")

    elif session_type == 'VOIP':
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)  # Needs camera/mic permissions
            context = browser.new_context(
                permissions=["microphone", "camera"]
            )
            page = context.new_page()

            print(f"Opening: {url}")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")

            try:
                print("Granting mic/camera and starting VOIP call...")

                # Click "Start" to initialize media devices
                page.click("text=Start", timeout=5000)
                time.sleep(1)

                # Click "Call" to begin peer connection
                page.click("text=Call", timeout=5000)
                print("VOIP call initiated. Streaming media...")

                # Let the call run for 30 seconds
                time.sleep(30)

                print("Ending the call.")
                page.click("text=Hang up", timeout=5000)

            except Exception as e:
                print(f"VOIP session failed: {e}")

            browser.close()
            print("VOIP session complete.")


    else:
        print(f"Session type '{session_type}' not supported.")


# simulate_network_session("https://en.wikipedia.org/wiki/Main_Page", "browsing")
# simulate_network_session("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "streaming")
# simulate_network_session("https://www.w3schools.com/howto/howto_html_file_upload_button.asp", "file_upload")
# simulate_network_session("https://file-examples.com/index.php/sample-documents-download/sample-pdf-download/", "file_download")
simulate_network_session("https://webrtc.github.io/samples/src/content/peerconnection/pc1/", "VOIP")


#     with open('encrypted_network_traffic.csv', 'w', newline='') as csvfile:
#         csv_writer = csv.writer(csvfile)
#         csv_writer.writerow([
#             'Timestamp', 'Source_IP', 'Source_port', 'Destination_IP', 'Destination_port', 'Protocol',
#             'fwd_packets_amount', 'bwd_packets_amount', 'fwd_packets_length', 'bwd_packets_length',
#             'max_fwd_packet', 'min_fwd_packet', 'max_bwd_packet', 'min_bwd_packet', 'FIN_count',
#             'SYN_count', 'RST_count', 'min_fwd_inter_arrival_time', 'max_fwd_inter_arrival_time',
#             'mean_fwd_inter_arrival_time', 'min_bwd_inter_arrival_time', 'max_bwd_inter_arrival_time',
#             'mean_bwd_inter_arrival_time', 'min_bib_inter_arrival_time', 'max_bib_inter_arrival_time',
#             'mean_bib_inter_arrival_time', 'first_packet_sizes_0', 'first_packet_sizes_1',
#             'first_packet_sizes_2', 'first_packet_sizes_3', 'first_packet_sizes_4',
#             'first_packet_sizes_5', 'first_packet_sizes_6', 'first_packet_sizes_7',
#             'first_packet_sizes_8', 'first_packet_sizes_9', 'first_packet_sizes_10',
#             'first_packet_sizes_11', 'first_packet_sizes_12', 'first_packet_sizes_13',
#             'first_packet_sizes_14', 'first_packet_sizes_15', 'first_packet_sizes_16',
#             'first_packet_sizes_17', 'first_packet_sizes_18', 'first_packet_sizes_19',
#             'first_packet_sizes_20', 'first_packet_sizes_21', 'first_packet_sizes_22',
#             'first_packet_sizes_23', 'first_packet_sizes_24', 'first_packet_sizes_25',
#             'first_packet_sizes_26', 'first_packet_sizes_27', 'first_packet_sizes_28',
#             'first_packet_sizes_29', 'min_packet_size', 'max_packet_size', 'mean_packet_size',
#             'STD_packet_size', 'mean_delta_byte', 'STD_delta_byte', 'bandwidth_0',
#             'bandwidth_1', 'bandwidth_2', 'bandwidth_3', 'bandwidth_4', 'bandwidth_5',
#             'bandwidth_6', 'bandwidth_7', 'bandwidth_8', 'bandwidth_9', 'bandwidth_10',
#             'bandwidth_11', 'bandwidth_12', 'bandwidth_13', 'bandwidth_14', 'bandwidth_15',
#             'bpp_0', 'bpp_1', 'bpp_2', 'beaconning_0', 'beaconning_1', 'beaconning_2',
#             'beaconning_3', 'beaconning_4', 'beaconning_5', 'pps_fwd', 'pps_bwd',
#             'count_big_requests', 'ACK_count', 'label'
#         ])

# if __name__ == '__main__':
#     main()
#
