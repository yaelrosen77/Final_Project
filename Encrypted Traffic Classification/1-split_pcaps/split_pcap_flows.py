import os
import subprocess

def split_pcap_by_streams(base_dir, output_dir, tshark_path="C:\\Program Files\\Wireshark\\tshark.exe"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".pcapng") or file.endswith(".pcap"):
                pcap_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, base_dir)
                ope_dir = os.path.join(output_dir, relative_path)

                if not os.path.exists(ope_dir):
                    os.makedirs(ope_dir)

                file_csv = file.replace(".pcapng", "").replace(".pcap", "")

                command = [
                    tshark_path, "-r", pcap_path, "-T", "fields", "-e", "tcp.stream", "-Y", "ssl.handshake"
                ]
                result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
                stream_ids = set(result.stdout.split())

                for stream_id in stream_ids:
                    output_pcap = os.path.join(ope_dir, f"{file_csv}_stream_{stream_id}.pcap")

                    output_subdir = os.path.dirname(output_pcap)
                    if not os.path.exists(output_subdir):
                        os.makedirs(output_subdir)

                    command = [
                        tshark_path, "-r", pcap_path, "-Y", f"tcp.stream == {stream_id}", "-w", output_pcap
                    ]
                    subprocess.run(command)
                    print(f"Saved stream {stream_id} to {output_pcap}")

base_dir = os.path.abspath("../0-pcap_datasets/mldit")
output_dir = "pcap_split_datasets\\mldit"
split_pcap_by_streams(base_dir, output_dir)
