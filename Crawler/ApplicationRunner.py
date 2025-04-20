from video_sniffer import sniff_all_videos, sniff_video
from voip_sniffer import sniff_all_voip
from cloud_sniffer import sniff_all_cloud
from download_sniffer import sniff_all_downloads
from browser_sniffer import sniff_all_browsing
from audio_sniffer import sniff_all_audios
def main():
    print("\n🎬 Capturing video traffic...")
    sniff_all_videos()

    print("\n🌐 Capturing browsing traffic...")
    sniff_all_browsing()

    print("\n🎮 Capturing Game traffic...")
    sniff_all_voip()

    print("\n📥 Capturing file download traffic...")
    sniff_all_downloads()

    print("\n☁️ Capturing cloud upload traffic...")
    sniff_all_cloud()

    print("\n☁️ Capturing Audio upload traffic...")
    sniff_all_audios()

    print("\n📞 Capturing VOIP traffic...")
    sniff_all_voip()

if __name__ == "__main__":
    main()
