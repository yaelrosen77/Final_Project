import os
import subprocess
import csv

def truncate_or_pad(data, max_length=32, fill_value=0):
    """Truncate or pad data to a fixed length."""
    if len(data) > max_length:
        return data[:max_length]
    else:
        return data + [fill_value] * (max_length - len(data))

def extract_flow_time_series(base_dir, output_dir, tshark_path="C:\\Program Files\\Wireshark\\tshark.exe"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".pcapng") or file.endswith(".pcap"):
                pcap_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, base_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                output_csv_path = os.path.join(output_subdir, f"{os.path.splitext(file)[0]}.csv")
                command = [
                    tshark_path, "-r", pcap_path, "-T", "fields",
                    "-e", "frame.time_delta",  # Time between packets
                    "-e", "frame.len",  # Packet size
                    "-e", "ip.src",  # Source IP
                    "-e", "ip.dst"  # Destination IP
                ]
                result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
                lines = result.stdout.strip().split("\n")
                packets = []
                for line in lines:
                    parts = line.split("\t")
                    if len(parts) < 4:
                        continue
                    time_delta = float(parts[0]) if parts[0] else 0
                    packet_size = int(parts[1]) if parts[1] else 0
                    src_ip = parts[2]
                    dst_ip = parts[3]
                    direction = 1 if src_ip < dst_ip else -1
                    packets.append([packet_size, time_delta, direction])
                packets_truncated = truncate_or_pad(packets, max_length=32, fill_value=[0, 0, 0])
                with open(output_csv_path, "w", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(["Packet Size", "Time Delta", "Direction"])
                    for packet in packets_truncated:
                        writer.writerow(packet)
                print(f"Flow time series for {file} extracted to {output_csv_path}")

base_dir = os.path.abspath("../1-split_pcaps/pcap_split_datasets")
output_dir = "pcap_csv_output_md"
extract_flow_time_series(base_dir, output_dir)
