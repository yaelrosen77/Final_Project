import socket
import requests
import csv
from scapy.all import sniff
from scapy.layers.inet import IP, TCP
import psutil
import time
from collections import defaultdict


def get_active_interface():
    """Find an active network interface that is enabled and operational and has an IP address."""
    interfaces = psutil.net_if_addrs()
    interface_stats = psutil.net_if_stats()

    for interface, addrs in interfaces.items():
        if interface in interface_stats and not interface_stats[interface].isup:
            continue

        for addr in addrs:
            if addr.family == socket.AF_INET and not addr.address.startswith("127."):
                print(f"[+] Using network interface: {interface}")
                return interface

    print("[-] No active network interface found.")
    return None


def generate_traffic(website):
    """Make a request to generate network traffic."""
    try:
        response = requests.get(f"https://{website}", timeout=5)
        print(f"[+] Request to {website} completed with status {response.status_code}")
    except requests.RequestException as e:
        print(f"[-] Failed to reach {website}: {e}")


def packet_filter(packet, csv_writer, packet_data):
    """Filter packets and write relevant information to CSV for encrypted traffic."""
    if IP in packet and TCP in packet:
        timestamp = time.time()
        src_ip = packet[IP].src
        dst_ip = packet[IP].dst
        length = len(packet)
        protocol = packet[IP].proto
        src_port = packet[TCP].sport if TCP in packet else None
        dst_port = packet[TCP].dport if TCP in packet else None

        # Initialize packet data for new source IP
        if src_ip not in packet_data:
            packet_data[src_ip] = defaultdict(int)  # Use defaultdict(int) for numeric counters
            packet_data[src_ip]['sizes'] = []  # Initialize list for packet sizes

        # Track packet size and inter-arrival time
        packet_data[src_ip]['sizes'].append(length)

        # Inter-arrival time
        if 'last_time' in packet_data[src_ip]:
            inter_arrival_time = timestamp - packet_data[src_ip]['last_time']
        else:
            inter_arrival_time = 0

        packet_data[src_ip]['last_time'] = timestamp

        # Additional packet statistics
        packet_data[src_ip]['fwd_packets_amount'] += 1
        packet_data[src_ip]['fwd_packets_length'] += length

        # Count specific flags (e.g., SYN, FIN)
        if TCP in packet:
            flags = packet[TCP].flags
            if 'S' in flags:
                packet_data[src_ip]['SYN_count'] += 1
            if 'F' in flags:
                packet_data[src_ip]['FIN_count'] += 1
            if 'R' in flags:
                packet_data[src_ip]['RST_count'] += 1
            if 'P' in flags:
                packet_data[src_ip]['PSH_count'] += 1

        # Write to CSV
        csv_writer.writerow([
            timestamp, src_ip, src_port, dst_ip, dst_port, protocol,
            packet_data[src_ip]['fwd_packets_amount'], packet_data[src_ip]['bwd_packets_amount'],
            packet_data[src_ip]['fwd_packets_length'], packet_data[src_ip]['bwd_packets_length'],
            max(packet_data[src_ip]['sizes']), min(packet_data[src_ip]['sizes']),
            packet_data[src_ip]['SYN_count'], packet_data[src_ip]['FIN_count'],
            packet_data[src_ip]['RST_count'], packet_data[src_ip]['PSH_count'],
            inter_arrival_time  # Add other features as needed
        ])
        print(f"[+] Packet from {src_ip} to {dst_ip} recorded at {timestamp}")


def capture_packets(iface, csv_writer):
    """Capture packets on the network interface."""
    if not iface:
        print("[-] No valid network interface. Exiting.")
        return []

    print(f"[+] Capturing packets on {iface}")
    packets = sniff(iface=iface, timeout=10)
    print(f"[+] Captured {len(packets)} packets.")

    packet_data = defaultdict(lambda: {
        'sizes': [],
        'fwd_packets_amount': 0,
        'bwd_packets_amount': 0,
        'fwd_packets_length': 0,
        'bwd_packets_length': 0,
        'SYN_count': 0,
        'FIN_count': 0,
        'RST_count': 0,
        'PSH_count': 0,
    })

    for packet in packets:
        packet_filter(packet, csv_writer, packet_data)

    return packets


def main():
    iface = get_active_interface()

    websites = ['google.com', 'youtube.com', 'facebook.com']

    with open('encrypted_network_traffic.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow([
            'Timestamp', 'Source_IP', 'Source_port', 'Destination_IP', 'Destination_port', 'Protocol',
            'fwd_packets_amount', 'bwd_packets_amount', 'fwd_packets_length', 'bwd_packets_length',
            'max_fwd_packet', 'min_fwd_packet', 'max_bwd_packet', 'min_bwd_packet', 'FIN_count',
            'SYN_count', 'RST_count', 'PSH_count', 'silence_windows', 'min_fwd_inter_arrival_time',
            'max_fwd_inter_arrival_time', 'mean_fwd_inter_arrival_time', 'min_bwd_inter_arrival_time',
            'max_bwd_inter_arrival_time', 'mean_bwd_inter_arrival_time', 'min_bib_inter_arrival_time',
            'max_bib_inter_arrival_time', 'mean_bib_inter_arrival_time', 'first_packet_sizes_0',
            'first_packet_sizes_1', 'first_packet_sizes_2', 'first_packet_sizes_3', 'first_packet_sizes_4',
            'first_packet_sizes_5', 'first_packet_sizes_6', 'first_packet_sizes_7', 'first_packet_sizes_8',
            'first_packet_sizes_9', 'first_packet_sizes_10', 'first_packet_sizes_11', 'first_packet_sizes_12',
            'first_packet_sizes_13', 'first_packet_sizes_14', 'first_packet_sizes_15', 'first_packet_sizes_16',
            'first_packet_sizes_17', 'first_packet_sizes_18', 'first_packet_sizes_19', 'first_packet_sizes_20',
            'first_packet_sizes_21', 'first_packet_sizes_22', 'first_packet_sizes_23', 'first_packet_sizes_24',
            'first_packet_sizes_25', 'first_packet_sizes_26', 'first_packet_sizes_27', 'first_packet_sizes_28',
            'first_packet_sizes_29', 'min_packet_size', 'max_packet_size', 'mean_packet_size', 'STD_packet_size',
            'mean_delta_byte', 'STD_delta_byte', 'bandwidth_0', 'bandwidth_1', 'bandwidth_2', 'bandwidth_3',
            'bandwidth_4', 'bandwidth_5', 'bandwidth_6', 'bandwidth_7', 'bandwidth_8', 'bandwidth_9',
            'bandwidth_10', 'bandwidth_11', 'bandwidth_12', 'bandwidth_13', 'bandwidth_14', 'bandwidth_15',
            'bandwidth_16', 'bandwidth_17', 'bandwidth_18', 'bandwidth_19', 'bpp_0', 'bpp_1', 'bpp_2',
            'beaconning_0', 'beaconning_1', 'beaconning_2', 'beaconning_3', 'beaconning_4', 'beaconning_5',
            'beaconning_6', 'beaconning_7', 'beaconning_8', 'beaconning_9', 'beaconning_10', 'beaconning_11',
            'beaconning_12', 'beaconning_13', 'beaconning_14', 'beaconning_15', 'beaconning_16', 'beaconning_17',
            'beaconning_18', 'beaconning_19', 'pps_fwd', 'pps_bwd', 'count_big_requests', 'ACK_count', 'label'
        ])

        for website in websites:
            generate_traffic(website)
            capture_packets(iface, csv_writer)


if __name__ == "__main__":
    main()
