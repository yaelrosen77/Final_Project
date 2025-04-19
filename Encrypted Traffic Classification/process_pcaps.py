import os
import subprocess
import pandas as pd
import csv


def truncate_or_pad(data, max_length, fill_value):
    """Truncate or pad data to a fixed length."""
    if len(data) > max_length:
        return data[:max_length]
    else:
        return data + [fill_value] * (max_length - len(data))

def extract_hex_per_packet(temp_hex_path):
    """Extract hex data per TLS packet from the TShark hex output."""
    packets = []
    current_packet = []
    with open(temp_hex_path, "r") as file:
        for line in file:
            if line.startswith("0000"):  # Begin collecting hex data
                current_packet.extend(line[6:54].split())
            elif current_packet and not line.strip():  # End of a packet
                packets.append(truncate_or_pad(current_packet,600,'00'))
                current_packet = []
            elif all(c in "0123456789abcdef" for c in line[:4].strip()):
                current_packet.extend(line[6:54].split())
        if current_packet:  # Append the last packet if it exists
            packets.append(truncate_or_pad(current_packet,600,'00'))
    return packets


class PcapProcessor:
    def __init__(self, base_dir, output_dir):
        self.base_dir = base_dir
        self.output_dir = output_dir
        self.stream_output_dir = "None"
        self.stream_pcap_path = "None"

    def extract_flow_time_series(self):
        """Extract flow time series for a given PCAP file."""
        command = [
            "tshark", "-r", self.stream_pcap_path, "-T", "fields",
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
        return pd.DataFrame(packets_truncated, columns=["Packet Size", "Time Delta", "Direction"])

    def extract_tls_header_to_csv(self):
        """Extract TLS headers to a DataFrame."""
        temp_csv = self.stream_pcap_path + "_tls.temp"
        temp_hex = self.stream_pcap_path + "_tls_hex.temp"

        # Extract TLS headers and hex data
        command_csv = [
            "tshark", "-r", self.stream_pcap_path, "-T", "fields",
            "-e", "frame.time_relative", "-e", "frame.len", "-e", "frame.time_delta",
            "-e", "ip.src", "-e", "ip.dst", "-e", "tcp.srcport", "-e", "tcp.dstport",
            "-e", "tls.record.content_type", "-e", "tls.handshake.type",
            "-e", "tls.handshake.session_id", "-e", "tls.record.version",
            "-e", "tls.record.length", "-e", "tls.handshake.extensions_server_name",
            "-Y", "ssl.handshake", "-E", "separator=,", "-E", "quote=d"
        ]
        command_hex = [
            "tshark", "-r", self.stream_pcap_path, "-x", "-Y", "ssl.handshake"
        ]

        with open(temp_csv, "w") as outfile:
            subprocess.run(command_csv, stdout=outfile)
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
                return features_df
            finally:
                os.remove(temp_csv)
                os.remove(temp_hex)
        return pd.DataFrame()

    def split_and_extract(self):
        """Split PCAPs by streams and extract TLS and flow time series data."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".pcapng") or file.endswith(".pcap"):
                    pcap_path = os.path.join(root, file)
                    relative_path = os.path.relpath(root, self.base_dir)
                    self.stream_output_dir = os.path.join(self.output_dir, relative_path)

                    if not os.path.exists(self.stream_output_dir):
                        os.makedirs(self.stream_output_dir)

                    file_csv = file.replace(".pcapng", "").replace(".pcap", "")

                    # Extract stream IDs
                    command = [
                        "tshark", "-r", pcap_path, "-T", "fields", "-e", "tcp.stream", "-Y", "ssl.handshake"
                    ]
                    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
                    stream_ids = set(result.stdout.split())

                    for stream_id in stream_ids:
                        self.stream_pcap_path = os.path.join(self.stream_output_dir,f"{file_csv}_stream_{stream_id}.pcap")

                        # Extract stream-specific packets
                        command = [
                            "tshark", "-r", pcap_path, "-Y", f"tcp.stream == {stream_id}", "-w", self.stream_pcap_path
                        ]
                        subprocess.run(command)

                        # Extract data
                        tls_df = self.extract_tls_header_to_csv()
                        md_df = self.extract_flow_time_series()

                        # Save to Excel
                        output_excel_path = self.stream_pcap_path.replace(".pcapng", ".xlsx").replace(".pcap", ".xlsx")
                        with pd.ExcelWriter(output_excel_path) as writer:
                            tls_df.to_excel(writer, sheet_name="TLS", index=False)
                            md_df.to_excel(writer, sheet_name="MD", index=False)

                        print(f"Processed stream {stream_id} to {output_excel_path}")

# Example usage
# base_dir = os.path.abspath("0-pcap_datasets/mldit")
# output_dir = "pcap_split_and_tls_output"
#
# processor = PcapProcessor(base_dir, output_dir)
# processor.split_and_extract()
