import psutil
import socket

# List all network interfaces and their associated IPs
for iface, addrs in psutil.net_if_addrs().items():
    print(f"Interface: {iface}")
    for addr in addrs:
        if addr.family == socket.AF_INET:
            print(f"  IP address: {addr.address}")
