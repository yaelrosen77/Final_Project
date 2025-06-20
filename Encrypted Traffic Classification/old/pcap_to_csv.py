import os
import subprocess
import pandas as pd
import numpy as np


def extract_pcap_labels(base_dir):
    data = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".pcapng") or file.endswith(".pcap"):
                # יצירת מסלול קובץ מלא
                file_path = os.path.join(root, file)

                # פירוק הנתיב לקטגוריות
                parts = file_path.split(os.sep)
                app_category = parts[-5]  # AppCategory
                app_protocol = parts[-4]  # AppProtocol
                navigator = parts[-3]  # Navigator
                operation = parts[-2]  # Operation

                # שמירת המידע
                data.append({
                    "file_path": file_path,
                    "app_category": app_category,
                    "app_protocol": app_protocol,
                    "navigator": navigator,
                    "operation": operation
                })

    return pd.DataFrame(data)

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

def filter_data(data):
    streams_with_handshake = data[
        data["tls_content_type"].astype(str).str.contains("22")
    ]["stream_id"].unique()

    filtered_df = data[
        data["stream_id"].isin(streams_with_handshake)
    ]
    filtered_df = filtered_df.groupby("stream_id").head(3).reset_index(drop=True)
    return filtered_df

def process_pcap_files(base_dir, output_dir, tshark_path=r"C:\Program Files\Wireshark\tshark.exe"):
    # יצירת DataFrame של תוויות
    labels_df = extract_pcap_labels(base_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # מעבר על כל קובצי ה-PCAP בתיקיות
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".pcapng") or file.endswith(".pcap"):
                pcap_path = os.path.join(root, file)
                relative_path = os.path.relpath(root, base_dir)
                file_csv = file.replace(".pcapng", ".csv").replace(".pcap", ".csv")
                output_csv = os.path.join(output_dir, f"{relative_path}_{file_csv}")

                output_subdir = os.path.dirname(output_csv)
                if not os.path.exists(output_subdir):
                    os.makedirs(output_subdir)

                print(f"Processing {pcap_path}...")
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
                    "-Y", "tls",  # מסנן TLS בלבד
                    "-E", "separator=,", "-E", "quote=d"
                ]
                command_hex = [
                    tshark_path, "-r", pcap_path, "-x", "-Y", "tls"
                ]

                temp_csv = output_csv + ".temp"
                temp_hex = output_csv + ".temp_hex"
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
                        features_df["stream_id"] = (
                                features_df["ip_src"] + ":" +
                                features_df["src_port"].astype(str) + "->" +
                                features_df["ip_dst"] + ":" +
                                features_df["dst_port"].astype(str)
                        )

                        features_df = filter_data(features_df)

                        label_row = labels_df[labels_df['file_path'] == pcap_path]
                        if not label_row.empty:
                            for col in ["app_category", "app_protocol", "navigator", "operation"]:
                                features_df[col] = label_row.iloc[0][col]

                        print(f"Saving CSV file: {output_csv}")
                        features_df.to_csv(output_csv, index=False)
                    except Exception as e:
                        print(f"Error processing {pcap_path}: {e}")
                    finally:
                        os.remove(temp_csv)
                        os.remove(temp_hex)


# הגדרת תיקיות קלט ופלט
base_dir = "C:\\Users\\Adam\\Desktop\\Project\\pcap_datasets\\mldit"
output_dir = "C:\\Users\\Adam\\Desktop\\Project\\csv_datasets\\mldit"

# קריאה לפונקציה
process_pcap_files(base_dir, output_dir)
