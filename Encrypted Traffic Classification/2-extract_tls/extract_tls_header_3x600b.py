import os
import subprocess
import csv
import pandas as pd
import numpy as np

def truncate_or_pad(data, max_length=600):
    """Truncate or pad data to 600 bytes."""
    if len(data) > max_length:
        return data[:max_length]
    else:
        return data + ['00'] * (max_length - len(data))

def extract_hex_per_packet(temp_hex_path):
    """
    Extract hex data per TLS packet from the TShark hex output.
    """
    packets = []
    current_packet = []
    with open(temp_hex_path, "r") as file:
        for line in file:
            if line.startswith("0000"):  # Begin collecting hex data
                current_packet.extend(line[6:54].split())
            elif current_packet and not line.strip():  # End of a packet
                packets.append(truncate_or_pad(current_packet))
                current_packet = []
            elif all(c in "0123456789abcdef" for c in line[:4].strip()):
                current_packet.extend(line[6:54].split())
        if current_packet:  # Append the last packet if it exists
            packets.append(truncate_or_pad(current_packet))
    return packets

def extract_tls_header_to_csv(base_dir, output_dir, tshark_path="C:\\Program Files\\Wireshark\\tshark.exe"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            # if 'AppCategory_AudioStreaming' in root: continue
            # if 'AppCategory_FileSharing' in root: continue
            # if 'AppCategory_Gaming' in root: continue
            # if 'AppCategory_InfoSites' in root: continue
            # if 'AppCategory_MarketPlace' in root: continue
            if file.endswith(".pcapng") or file.endswith(".pcap"):
                pcap_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, base_dir)
                output_subdir = os.path.join(output_dir, relative_path)
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)
                file_csv = file.replace(".pcapng", "").replace(".pcap", "")
                output_csv_path = os.path.join(output_subdir, f"{file_csv}.csv")
                temp_csv = output_csv_path + ".temp"
                temp_hex = output_csv_path + ".temp_hex"

                command = [
                    tshark_path, "-r", pcap_path, "-T", "fields",
                    "-e", "frame.time_relative",  # זמן יחסי
                    "-e", "frame.len",  # גודל חבילה
                    "-e", "frame.time_delta",  # זמן יחסית לחבילה הקודמת
                    "-e", "ip.src",  # IP מקור
                    "-e", "ip.dst",  # IP יעד
                    "-e", "tcp.srcport",  # פורט מקור
                    "-e", "tcp.dstport",  # פורט יעד
                    "-e", "tls.record.content_type",  # סוג רשומה TLS
                    "-e", "tls.handshake.type",  # סוג Handshake (ClientHello, ServerHello)
                    "-e", "tls.handshake.session_id",  # מזהה Session ID
                    "-e", "tls.record.version",  # גרסת TLS
                    "-e", "tls.record.length",  # אורך TLS Record
                    "-e", "tls.handshake.extensions_server_name",  # SNI אם קיים
                    "-Y", "ssl.handshake",
                    "-E", "separator=,", "-E", "quote=d"
                ]
                command_hex = [
                    tshark_path, "-r", pcap_path, "-x", "-Y", "ssl.handshake"
                ]

                with open(temp_csv, "w") as outfile:
                    subprocess.run(command, stdout=outfile)
                with open(temp_hex, "w") as outfile:
                    subprocess.run(command_hex, stdout=outfile)
                if os.path.exists(temp_csv):
                    try:
                        features_df = pd.read_csv(temp_csv, names=[
                            "time_relative", "frame_len", "time_delta",
                            "ip_src", "ip_dst", "src_port", "dst_port",
                            "tls_content_type", "tls_handshake_type",
                            "tls_session_id", "tls_version", "tls_record_length",
                            "tls_sni"
                        ])
                        features_df['tls_content'] = extract_hex_per_packet(temp_hex)
                        top_3_df = features_df.head(3).reset_index(drop=True)
                        top_3_df.to_csv(output_csv_path, index=False)
                    except Exception as e:
                        print(f"Error processing {pcap_path}: {e}")
                    finally:
                        os.remove(temp_csv)
                        os.remove(temp_hex)
# דוגמה לשימוש
base_dir = os.path.abspath("../1-split_pcaps/pcap_split_datasets")
output_dir = "pcap_csv_output_tls"
extract_tls_header_to_csv(base_dir, output_dir)
